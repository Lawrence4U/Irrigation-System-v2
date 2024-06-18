#include <Adafruit_MCP23X17.h>
#include <Adafruit_MCP23XXX.h>
#include <RTCZero.h>
#include <MKRWAN_v2.h>
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

//temp sensor addresses
// #define ADDR_TEMP 0b1001000
// #define TEMP_READ 0b0

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
#define NUM_REALYS 2
#define NUM_RESERVE_PER 1

LoRaModem modem; // handles LoRa connectivity and messaging
RTCZero rtc; // handles RTC module
Adafruit_MCP23X17 expander1, expander2; // object to handle I2C communications with expanders as a regular microcontroller with digitalREad/Write etc functions

String appEui = SECRET_APP_EUI;
String appKey = SECRET_APP_KEY;

// struct to handle each analog sensor and store its value
typedef struct {
    const int read_pin;
    const int enable_pin;
    double value;
} AnalogSensor;

typedef enum{
  Expander1,
  Expander2,
}Expander;

// struct to handle each peripheral conected to the L298. Default behaviour will be current from pin1 to pin2
typedef struct {
  const int enable_pin;
  const int pin1;
  const int pin2;
} L298_Peripheral;

// Initialize all sensors and value storage
AnalogSensor sens_hum[NUM_HUM_SENSOR] = {{S_HUM_1_IN, S_HUM_1_EN, -1},{S_HUM_2_IN, S_HUM_2_EN, -1},{S_HUM_3_IN, S_HUM_3_EN, -1}}; 
AnalogSensor sens_anemom[NUM_ANEMOM] = {{S_ANEM_IN, NULL, -1}};
double temp_values[NUM_TEMP_SENSOR] = {-1};
double light_values[NUM_LIGHT_SENSOR] = {-1};

// Initialize all actuators. No need to add references to the assigned expander since each array is contained in the same expander
L298_Peripheral pumps[NUM_PUMPS] = {{P1_EN, P1_IN1, P1_IN2},{P2_EN, P2_IN1, P2_IN2},{P3_EN, P3_IN1, P3_IN2},{P4_EN, P4_IN1, P4_IN2},{P5_EN, P5_IN1, P5_IN2}};
L298_Peripheral windows[NUM_WINDOWS] = {{W1_EN, W1_IN1, W1_IN2},{W2_EN, W2_IN1, W2_IN2}};
L298_Peripheral reserve[NUM_RESERVE_PER] = {{R1_EN, R1_IN1, R1_IN2}};
int relays[NUM_REALYS] = {RELAY_1_EN, RELAY_2_EN};

// Function definitions
  //sensor related
void setupAnalogSensors(const AnalogSensor sensors[], int num_sensors); // setup sensors
double readAnalogSensor(const AnalogSensor sensor); // read sensor value multiple times and return average
double processHumidityData(double readValue); // transform analog value to humidity percentage
double processWindData(double readValue); // transform analog value to wind speed in m/s
  //expander and actuator related
void setPinModes(Adafruit_MCP23X17 expander, L298_Peripheral peripherals[], int size, bool direction); // set all pinModes sequentially

void togglePin(int pin){
  pinMode(pin, OUTPUT);
  digitalWrite(pin, HIGH);
  delay(500);
  digitalWrite(pin, LOW);
  Serial.println("pin" + String(pin) +  "toggled");
  return;  
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);
  // change this to your regional band (eg. US915, AS923, ...)
  // if (!modem.begin(EU868)) {
  //   Serial.println("Failed to start module");
  //   while (1) {}
  // };
  // Serial.print("Your module version is: ");
  // Serial.println(modem.version());
  // Serial.print("Your device EUI is: ");
  // Serial.println(modem.deviceEUI());

  // int connected = modem.joinOTAA(appEui, appKey);
  // if (!connected) {
  //   Serial.println("Something went wrong; are you indoor? Move near a window and retry");
  //   while (1) {}
  // }

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
    Serial.println("Error initializing expander 1.");
    while (1);
  }
    // pinmodes
  setPinModes(expander1, pumps, NUM_PUMPS, OUTPUT);
  setPinModes(expander2, windows, NUM_WINDOWS, OUTPUT);
  setPinModes(expander2, reserve, NUM_RESERVE_PER, OUTPUT);
  for(int i=0; i<NUM_REALYS; i++){
    expander2.pinMode(relays[i], OUTPUT);
  }

  
}

double temp_required = -1;
double light_required = -1;
bool activate_lights = false;
bool open_windows = false;
bool open_valves = false;

void loop() {
  //send init message, server returns current workload

    //setup program

      

  // activate required peripherals
    //heater
  double temp_avg = 0;
  for(int i=0; i<NUM_TEMP_SENSOR;i++){
    temp_avg+=temp_values[i];
  }
  digitalWrite(HEAT_EN, temp_avg < temp_required); //activate heater if temp less than expected, else turn off

    //lighting
  double light_avg = 0;
  for(int i=0; i<NUM_LIGHT_SENSOR;i++){
    light_avg+=light_values[i];
  }
  digitalWrite(FOCO1_EN, light_avg < light_required); //turn on lighting if not enough ambient
  digitalWrite(FOCO2_EN, light_avg < light_required);
  digitalWrite(FOCO3_EN, light_avg < light_required);
  digitalWrite(FOCO4_EN, light_avg < light_required);
    //windows
  
    //pumps
    //relays / blinds

  //read sensors and store values

    //humidity
  for(int i=0; i<NUM_HUM_SENSOR; i++){
    sens_hum[i].value = processHumidityData(readAnalogSensor(sens_hum[i]));
  }
    //anemometer
  for(int i=0; i<NUM_ANEMOM; i++){
    sens_anemom[i].value = processWindData(readAnalogSensor(sens_anemom[i]));
  }
    //read values sent from slave board

  
  //send values

  Serial.println(analogRead(A1));
  delay(500);
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
  if( voltage < 0.4) { return 0; }
  if( voltage > 2) { return 32.4; }
  return (voltage-0.4)*32.4 / (2-0.4); // translation from one range to another
}

void setPinModes(Adafruit_MCP23X17 expander, L298_Peripheral peripherals[], int size, bool direction){
  for(int i=0; i<size; i++){
    expander.pinMode(peripherals[i].enable_pin, direction);
    expander.pinMode(peripherals[i].pin1, direction);
    expander.pinMode(peripherals[i].pin2, direction);
  }
}

























