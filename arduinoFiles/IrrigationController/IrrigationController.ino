#include <MKRWAN_v2.h>
#include <I2C_16Bit.h>
#include <Wire.h>
#include "arduino_secrets.h"

// analog pins definition A#
#define S_HUM_1_IN 0
#define S_HUM_2_IN 1
#define S_HUM_3_IN 2
#define S_ANEM_IN  4

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

//expander addresses IOCON.BANK = 0
#define ADDR_EXP_1 0b0100000
#define ADDR_EXP_2 0b0100001
#define GPIOA 0x12 //value of pins 7-0
#define GPIOB 0x13
#define IODIR_A 0x00 // direction of pins 7-0. Def 1
#define IODIR_B 0x01 // [0,1] -> [output,input]


//temp sensor addresses
// #define ADDR_TEMP 0b1001000
// #define TEMP_READ 0b0

//pin addresses of I/O expander EXP_1
// B
#define P1_EN   0
#define P1_IN1  1
#define P1_IN2  2
#define P2_EN   3
#define P2_IN1  4
#define P2_IN2  5
#define P5_IN1  6
#define P5_IN2  7
//A
#define P5_EN  0
#define P4_EN  1
#define P4_IN1 2
#define P4_IN2 3
#define P3_EN  4
#define P3_IN1 5
#define P3_IN2 6

//pin addresses EXP_2
//A
#define W2_EN   0
#define W2_IN1  1
#define W2_IN2  2
#define W1_EN   3
#define W1_IN1  4
#define W1_IN2  5
//B
#define R1_EN      0
#define R1_IN1     1
#define R1_IN2     2
#define RELAY_1_EN 6
#define RELAY_2_EN 7

LoRaModem modem;
RTCZero rtc;

String appEui = SECRET_APP_EUI;
String appKey = SECRET_APP_KEY;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial);
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

  modem.minPollInterval(60);

}

void loop() {

}