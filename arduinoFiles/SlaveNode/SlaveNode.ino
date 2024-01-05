#include <Wire.h>

#define MOSI 11
#define MISO 12
#define SCK 13
#define RESET 19
#define SDA 17
#define SCL 18

#define TMP75_ADDR 0x4F
#define TMP_READ_ADDR 0x00
#define TMP_CONF_ADDR 0x01
#define TMP_CONF_VAL 0b0110000
#define LIGHT_ADDR 0x10

#define REQUEST 0x2A

char buffer[64];
int rcvIndex = 0;
bool newData = false;
bool send_res = false;
char collected_data[32];


void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Ready\n");

  Wire.begin();
}

void loop() {
  rcvIndex = 0;
  buffer[0] = '\0';

  //Read Order
  while (Serial.available()) {
    buffer[rcvIndex] = Serial.read();
    newData = true;
    rcvIndex++;
  }

  //Process
  if (newData) {
    if (strstr(buffer, REQUEST) != NULL) {
      //preparar collected_data
      collected_data = readSensors();
      send_res = true;
    }
  }

  //Response
  if (send_res) {
    Serial.println(collected_data);
    send_res = false;
  }

}

void startTmp(){
  Wire.beginTransmission(TMP75_ADDR);
  Wire.write(TMP_CONF_ADDR);
  Wire.write(TMP_CONF_VAL);
  Wire.endTransmission();
}

int readTemp(){
  int value = -99;
  Wire.beginTransmission(TMP75_ADDR);
  Wire.write(TMP_READ_ADDR);
  Wire.endTransmission();

  Wire.requestFrom(TMP75_ADDR,2);
  delay(300);//Bit resolution sets a max conversion time of 300ms

  rcvIndex=0;
  if(Wire.available()<=2){
    while(Wire.available()){
      buffer[rcvIndex] = Serial.read();
      rcvIndex++;
    }
    rcvIndex=0;
  }
  value = buffer[0] | buffer[1] << 8;
  Serial.println(value);
  return value;
}
