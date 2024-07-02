#include <serialProtocol.h>
#include <Adafruit_MCP23X17.h>
#include <Adafruit_MCP23XXX.h>
#include <RTCZero.h>
#include <MKRWAN.h>
#include "arduino_secrets.h"

// analog pins definition A#
#define S_HUM_1_IN A0
#define S_HUM_2_IN A1
#define S_HUM_3_IN A2
#define S_ANEM_IN  A4

//digital pins D#
#define S_HUM_1_EN 0
#define S_HUM_2_EN 1
#define S_HUM_3_EN 2
#define PULSE_IN 4
#define HEAT_EN 5
#define FOCO1_EN 6
#define FOCO2_EN 7
#define FOCO3_EN 8
#define FOCO4_EN 9
#define SDA 11
#define SCL 12

//expander addresses IOCON.BANK = 0. Default is 0 and sequential enabled
#define ADDR_EXP_1 0b0100000
#define ADDR_EXP_2 0b0100001
#define GPIOA 0x12 //value of pins 7-0
#define GPIOB 0x13
#define IODIR_A 0x00 // direction of pins 7-0. Def 1
#define IODIR_B 0x01 // [0,1] -> [output,input]
#define IOCON_CONFIG 0b00001000 //set HAEN 1 to enable addressing through pins

//pin addresses of I/O expander EXP_1
//GPIOB
#define P1_EN   0 + 8 //in Adafruit_MCP23X17 libray GPIOA has 0-7 pins and B 8-15
#define P1_IN1  1 + 8
#define P1_IN2  2 + 8
#define P2_EN   3 + 8
#define P2_IN1  4 + 8
#define P2_IN2  5 + 8
#define P5_IN1  6 + 8
#define P5_IN2  7 + 8
//GPIOA
#define P5_EN  0
#define P4_EN  1
#define P4_IN1 2
#define P4_IN2 3
#define P3_EN  4
#define P3_IN1 5
#define P3_IN2 6

//pin addresses EXP_2
//GPIOA
#define W2_EN   0
#define W2_IN1  1
#define W2_IN2  2
#define W1_EN   3
#define W1_IN1  4
#define W1_IN2  5
//GPIOB
#define R1_EN      0 + 8
#define R1_IN1     1 + 8
#define R1_IN2     2 + 8
#define RELAY_1_EN 6 + 8
#define RELAY_2_EN 7 + 8

// arrays size constants for easier scaling in case of changes
#define NUM_HUM_SENSOR 3
#define NUM_ANEMOM 1
#define NUM_TEMP_SENSOR 1
#define NUM_LIGHT_SENSOR 1
#define NUM_SENSORS NUM_HUM_SENSOR + NUM_LIGHT_SENSOR + NUM_ANEMOM + NUM_TEMP_SENSOR

#define NUM_PUMPS 5
#define NUM_WINDOWS 2
#define NUM_RELAYS 2
#define NUM_RESERVE_PER 1
const unsigned long OFFSET = 420000;//7minutes in mills

LoRaModem modem; // handles LoRa connectivity and messaging
RTCZero rtc; // handles RTC module
Adafruit_MCP23X17 expander1, expander2; // object to handle I2C communications with expanders as a regular microcontroller with digitalREad/Write etc functions

String appEui = SECRET_APP_EUI;
String appKey = SECRET_APP_KEY;

//structs for handling actions and structuring them in time
typedef struct{
  byte hour;
  byte minute;
  byte second;
}Time;

// struct to handle each analog sensor and store its value
typedef struct {
    const int read_pin;
    const int enable_pin;
    double value;
} AnalogSensor;



// struct to handle each peripheral conected to the L298. Default behaviour will be current from pin1 to pin2
typedef struct {
  int enable_pin;
  int pin1;
  int pin2;
} L298_Peripheral;

typedef struct{
  Time hour; //hour of action
  L298_Peripheral actuator; //which peripheral to toggle
  int value; //in case of extra values to add
  bool direction; // whether is action to start or stop
} PeripherialAction;

PeripherialAction plannedActions[7][30];
int num_actions[7] = {0,0,0,0,0,0,0};
int action_selected[7] = {0,0,0,0,0,0,0};

// Initialize all sensors and value storage
AnalogSensor sens_hum[NUM_HUM_SENSOR] = {{S_HUM_1_IN, S_HUM_1_EN, -1},{S_HUM_2_IN, S_HUM_2_EN, -1},{S_HUM_3_IN, S_HUM_3_EN, -1}}; 
AnalogSensor sens_anemom[NUM_ANEMOM] = {{S_ANEM_IN, NULL, -1}};
double temp_values[NUM_TEMP_SENSOR] = {-1};
double light_values[NUM_LIGHT_SENSOR] = {-1};

// Initialize all actuators. No need to add references to the assigned expander since each array is contained in the same expander
L298_Peripheral pumps[NUM_PUMPS] = {{P1_EN, P1_IN1, P1_IN2},{P2_EN, P2_IN1, P2_IN2},{P3_EN, P3_IN1, P3_IN2},{P4_EN, P4_IN1, P4_IN2},{P5_EN, P5_IN1, P5_IN2}};
L298_Peripheral windows[NUM_WINDOWS] = {{W1_EN, W1_IN1, W1_IN2},{W2_EN, W2_IN1, W2_IN2}};
L298_Peripheral reserve[NUM_RESERVE_PER] = {{R1_EN, R1_IN1, R1_IN2}};
L298_Peripheral relays[NUM_RELAYS] = {{RELAY_1_EN, NULL, NULL}, {RELAY_2_EN, NULL, NULL}};

// Function definitions
  //sensor related
void setupAnalogSensors(const AnalogSensor sensors[], int num_sensors); // setup sensors
double readAnalogSensor(const AnalogSensor sensor); // read sensor value multiple times and return average
double processHumidityData(double readValue); // transform analog value to humidity percentage
double processWindData(double readValue); // transform analog value to wind speed in m/s
  //expander and actuator related
void setPinModes(Adafruit_MCP23X17 expander, L298_Peripheral peripherals[], int size, bool direction); // set all pinModes sequentially
void togglePeripheral(Adafruit_MCP23X17 expander, L298_Peripheral peripheral, bool direction);

void togglePin(int pin){
  pinMode(pin, OUTPUT);
  digitalWrite(pin, HIGH);
  delay(500);
  digitalWrite(pin, LOW);
  Serial.println("pin" + String(pin) +  "toggled");
  return;  
}

char buffLora[256];
char buffSerial[64];
unsigned long timer_start = 0;
double temp_required = -1;
long int light_required;
SensorData rcv_data; 
float curr_temperature =-1;
float curr_light = -1;
byte day_of_week = 0; //a bit from 0 to 7 will be up based on which dya of week it is


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200); // for debug
  Serial1.begin(9600); // for rs422 communication
  while (!Serial);
  while(!Serial1);
  // change this to your regional band (eg. US915, AS923, ...)
  if (!modem.begin(EU868)) {
    Serial.println("Failed to start module");
    while (1) {}
  };
  Serial.print("Your module version is: ");
  Serial.println(modem.version());
  Serial.print("Your device EUI is: ");
  Serial.println(modem.deviceEUI());

  int connected = modem.joinOTAA(appEui, appKey);
  if (!connected) {
    Serial.println("Something went wrong; are you indoor? Move near a window and retry");
    while (1) {}
  }

  // modem.minPollInterval(60);

  // setup humidity sensors
  setupAnalogSensors(sens_hum, NUM_HUM_SENSOR);
  // setup anemometer
  setupAnalogSensors(sens_anemom, NUM_ANEMOM);

  // setup expanders and actuators
  if (!expander1.begin_I2C(ADDR_EXP_1)) {
    Serial.println("Error initializing expander 1.");
    while (1);
  }
  if (!expander2.begin_I2C(ADDR_EXP_2)) {
    Serial.println("Error initializing expander 2.");
    while (1);
  }
    // pinmodes
  setPinModes(expander1, pumps, NUM_PUMPS, OUTPUT);
  setPinModes(expander2, windows, NUM_WINDOWS, OUTPUT);
  setPinModes(expander2, reserve, NUM_RESERVE_PER, OUTPUT);
  setPinModes(expander2, relays, NUM_RELAYS, OUTPUT);

  //send init message, server returns current workload
  Serial.println("Waiting for messages");
  char mensaje[5] = "Init";
  while(!modem.available()){ //ping init message until program is received
    sendMessage(mensaje, 4);
    delay(20000); // 2 minute delay to not surpass send limits
  }
  //setup workload
  Serial.println("Received workload");
  int i=0;
  while (modem.available()) {
    buffLora[i++] = (char)modem.read();
  }
  buffLora[i++] = '/0'; 

  printBinaryData(buffLora, i++);
  
  manageConfig(buffLora);
  timer_start = millis();

}



void loop() {
  // check when a day passes, update current_day var + structure the actions for the day

  //check new messages
  int i=0;
  if(modem.available()){
    while (modem.available()) {
      buffLora[i++] = (char)modem.read();
    }
    buffLora[i++] = '/0'; 
    printBinaryData(buffLora, i++);
    //setup program
    manageConfig(buffLora);
  }
  //read sensors and store values

    //humidity
  for(int i=0; i<NUM_HUM_SENSOR; i++){
    sens_hum[i].value = processHumidityData(readAnalogSensor(sens_hum[i]));
  }
    //anemometer
  for(int i=0; i<NUM_ANEMOM; i++){
    sens_anemom[i].value = processWindData(readAnalogSensor(sens_anemom[i]));
  }

  //read serial data and save it
  while(Serial1.available() > 7){
    Serial1.readBytes(buffSerial, 8); //read complete messages
    processSerialData(&rcv_data, buffSerial); 
    switch (rcv_data.sens_type){
      case TEMPERATURE:
        curr_temperature = rcv_data.value;
        break;
      case LIGHT:
        curr_light = rcv_data.value;
        break;
      default:
        Serial.println("Error in sensor packet");
        break;
    }
  }

  //send values if enoughh time passed
  if(millis() - timer_start >= OFFSET){
      timer_start = millis();

      //compile data into packet

      //send packet
  }
  
  // activate required peripherals
    //heater
  double temp_avg = 0;
  for(int i=0; i<NUM_TEMP_SENSOR;i++){
    temp_avg+=temp_values[i];
  }
  digitalWrite(HEAT_EN, temp_avg < temp_required); //activate heater if temp less than expected, else turn off

    //lighting

    //windows
  
    //pumps
    //relays / blind

}

void setupAnalogSensors(const AnalogSensor sensors[], int size){
  for(int i=0; i<size; i++){
    pinMode(sensors[i].read_pin, INPUT);
    pinMode(sensors[i].enable_pin, OUTPUT);
    digitalWrite(sensors[i].enable_pin, LOW);
  }
}

double readAnalogSensor(const AnalogSensor sensor){
  int polling = 0;
  const int NUM_POLLS = 4;

  if(sensor.enable_pin != NULL){
    digitalWrite(sensor.enable_pin, HIGH);
  }

  delay(20);
  for(int i=0;i<NUM_POLLS;i++){
    polling = polling + analogRead(sensor.read_pin);
  }

  if(sensor.enable_pin != NULL){
    digitalWrite(sensor.enable_pin, LOW);
  }
  return polling/NUM_POLLS; 
}

double processHumidityData(double readValue){
  double hum_prcnt;
  double voltage = readValue*3.33/4096; // read to voltage
  voltage = voltage*1000/0.638; // to mV and factor in voltage divider
  hum_prcnt = .439*pow(10,-10)*pow(voltage,3) -2.731*pow(10,-6)*pow(voltage,2) +4.868*pow(10, -3)*voltage -2.683; //vootage to himdity formula
  return hum_prcnt;
}

double processWindData(double readValue){
  double voltage = readValue*3.33/1024;
  // voltage range for anemometer = (.4, 2)
  // wind range according to voltage = (0, 32.4). According to datasheet: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/717/1733_Web.pdf 
  if( voltage < 0.35) { return 0; }
  if( voltage > 2) { return 32.4; }
  double wind_ms = (voltage-0.35)*32.4 / (2-0.35); // translation from one range to another
  return round(wind_ms * 10) / 10.0; // return rounded to first decimal
}

void setPinModes(Adafruit_MCP23X17 expander, L298_Peripheral peripherals[], int size, bool direction){
  for(int i=0; i<size; i++){
    expander.pinMode(peripherals[i].enable_pin, direction);
    expander.pinMode(peripherals[i].pin1, direction);
    expander.pinMode(peripherals[i].pin2, direction);
  }
}

void togglePeripheral(Adafruit_MCP23X17 expander, L298_Peripheral peripheral, bool direction){
  //has to acomodate relays, and value based peripherals
  expander.digitalWrite(peripheral.enable_pin, HIGH);
  expander.digitalWrite(peripheral.pin1, direction);
  expander.digitalWrite(peripheral.pin2, !direction);
}

int sendMessage(char *message, int longitud){
  char *pt_msg = message;
  Serial.print("Sending:");
  for (int i = 0; i < longitud; i++) {
    Serial.print(*pt_msg >> 4, HEX);
    Serial.print(*pt_msg & 0xF, HEX);
    pt_msg++;
    Serial.print(" ");
  }
  Serial.println();
  int succ = 0;
  modem.beginPacket();
  while(!succ){
    modem.print(message);
    succ = modem.endPacket(true);
    if (succ > 0) {
      Serial.println("Message sent correctly!");
      return 1;
    } else {
      Serial.println("Error sending message :(");
      return 0;
    }
  }
}

void printBinaryData(char* buffer, int length){
  Serial.print("Message Received: ");
  for (int j = 0; j < length; j++) {
    Serial.print(buffer[j] >> 4, HEX);
    Serial.print(buffer[j] & 0xF, HEX);
    Serial.print(" ");
  }
  Serial.print("\n");
}

// Reads info in message, sets up variables and alarms
void manageConfig(char *buffer){ 
  const int ORDER_BYTE_LENGTH = 5;
  const int OBJ_BYTE_LENGTH = 3;

  //read general parameters
  uint8_t current_day = ((buffer[0] & 0xF8) >> 3);  
  uint8_t current_month = ((buffer[0] & 0x7) << 1) | ((buffer[1] & 0x80)>>7);
  uint8_t current_year = buffer[1] & 0x7F;
  uint8_t current_hour = (buffer[2] & 0xF8) >>3;
  uint8_t current_minute = ((buffer[2] & 0x7) << 3) | ((buffer[3] & 0xE0)>>5);
  uint8_t day_of_week = ((buffer[3] & 0x1F) <<2) | ((buffer[4] & 0xC0)>>6);
  uint8_t num_orders = (buffer[4] & 0x3C) >>2;

  //read orders
  char *order_ptr = &buffer[5];
  for(int i=0; i< num_orders; i++){
    //read each var and store the actions in the array
    readOrder(&order_ptr[i*ORDER_BYTE_LENGTH]);
  }
  //sort each day
  sortActions();

  //read objectives
  char *obj_ptr = &order_ptr[num_orders*5];
  uint8_t num_objectives = obj_ptr[0]>>4;
  uint8_t reserved2 = obj_ptr[0] & 0xF;
  for(int i=0; i< num_objectives; i++){
    //read each var and store the actions in the array
    readObjective(&obj_ptr[i*OBJ_BYTE_LENGTH]);
  }

  //update rtc clock
  rtc.setTime(current_hour, current_minute, 0);
  rtc.setDate(current_day, current_month, current_year);
}

void readOrder(char *data){
  //read each field
  uint8_t actuator_type = (data[0] & 0xF0) >> 4;
  uint8_t days_of_week = ((data[0] & 0x0F) << 3) | ((data[1] & 0xD0) >>5);
  uint8_t hour_start = data[1] & 0x1F;
  uint8_t minute_start = (data[2] & 0xFC) >> 2;
  uint8_t hour_duration = ((data[2] & 0x3) << 3) | ((data[3] & 0xE0)>>5);
  uint8_t minute_duration = ((data[3] & 0x1F) << 1) | ((data[4] & 0x80)>>7);
  uint8_t value = data[4] & 0x9F;

  // create actions from packet data
  Time start;
  start.hour = hour_start;
  start.minute = minute_start;
  start.second = 0;
  uint8_t act_value = (value==0) ? NULL : value; //if val is 0 the toggle will be different

  //get the peripheral
  L298_Peripheral per;
  if(actuator_type < 5){ //pump
    per = pumps[actuator_type];
  }else if(actuator_type < 7){ //windows
    per = windows[actuator_type];
  }else if(actuator_type < 8){ //reserve
    per = reserve[actuator_type];
  }else if(actuator_type < 10){ //relays
    per = relays[actuator_type];
  }

  PeripherialAction act1;
  act1.hour = start;
  act1.actuator = per;
  act1.value = act_value;
  act1.direction = true;

  //store the starting action in the actions array in corresponding days
  for(int day=0;day<7;day++){
    if((days_of_week>>day) & 0x1){
      while(timeSlotOcuppied(act1.hour, day)){ //check timeslot doesnt match with any other actions
        act1.hour.second += 10;
        if(act1.hour.second >= 60){
          act1.hour.second =0;
          act1.hour.minute +=1;
        }
      }
      plannedActions[day][num_actions[day]++] = act1;
    }
  }

  PeripherialAction act2;
  Time stop = start;
  //take care of possible time overflows
  if(stop.minute + minute_duration > 59){
    stop.hour++;
    stop.minute = stop.minute + minute_duration - 60;
  }
  if(stop.hour + hour_duration > 23){
    stop.hour = stop.hour + hour_duration - 24;
    if(days_of_week & 0x1){
      days_of_week = (days_of_week >> 1) | 0x40;
    }else{
      days_of_week = days_of_week >> 1;
    }
  }

  act2.hour = stop;
  act2.actuator = per;
  act2.value = act_value;
  act2.direction = false;

  for(int day=0;day<7;day++){
    if((days_of_week>>day) & 0x1){
      while(timeSlotOcuppied(act2.hour, day)){
        act2.hour.second += 10;
        if(act2.hour.second >= 60){
          act2.hour.second =0;
          act2.hour.minute +=1;
        }
      }
      plannedActions[day][num_actions[day]++] = act2;
    }
  }
}


void readObjective(char *data){
  //read each field
  uint8_t actuator_type = (data[0] & 0xF0) >> 4;
  uint32_t objective_value = ((data[0] & 0x0F) << 16) | (data[1]<<8) | (data[2]<<8);

  if(actuator_type < 12){ //error
    Serial.println("Error on obj packet peripheral id");// actuator id not valid for objectives
  }else if(actuator_type < 13){ //heater
    temp_required = objective_value / 100.0;
  }else if(actuator_type < 17){ //lighting
    light_required = objective_value;
  }
}


// this function is used to ensure two devices dont start at the same time. For high power utilities like valves this is a must to prevent overloading the regulator
bool timeSlotOcuppied(Time start_time, int day_index){
  for(int i=0;i<num_actions[day_index];i++){
    if(start_time.hour == plannedActions[day_index][i].hour.hour && start_time.minute == plannedActions[day_index][i].hour.minute && start_time.second == plannedActions[day_index][i].hour.second){
      return true;  
    }
  }
  return false;
}


void sortActions(){
  for(int day=0; day<7; day++){
    for (int i=0; i<num_actions[day];i++){
      for(int j=0; j<num_actions[day]-i-1; j++){
        if(!comesBefore(plannedActions[day][j], plannedActions[day][j+1])){ //si acciones[j] es antes devolvera un 1 => no se cambia
          swap(&plannedActions[day][j], &plannedActions[day][j+1]);  
        }
      }
    }
  }
  return;
}

bool comesBefore(const PeripherialAction action1, const PeripherialAction action2){ 
  if(action1.hour.hour < action2.hour.hour){ 
     return true; 
  }else if(action1.hour.hour == action2.hour.hour && action1.hour.minute < action2.hour.minute){
    return true;  
  }else if(action1.hour.hour == action2.hour.hour && action1.hour.minute == action2.hour.minute && action1.hour.second < action2.hour.second){
    return true;  
  }
  return false; 

}

void swap(PeripherialAction *xp, PeripherialAction *yp){
    PeripherialAction temp = *xp;
    *xp = *yp;
    *yp = temp;
    return;
}
















