#include <MKRWAN_v2.h>
#include <I2C_16Bit.h>
#include <Wire.h>
#include "arduino_secrets.h"

// analog pins definition
#define S_HUM_1_IN 0
#define S_HUM_2_IN 1
#define S_HUM_3_IN 2
#define S_ILUM_IN  3
#define S_ANEM_IN  4

//digital pins
#define S_HUM_1_EN 0
#define S_HUM_2_EN 1
#define S_HUM_3_EN 2
#define S_ILUM_EN 3
#define S_ANEM_EN 4
#define FOCO_EN 5
#define HEAT_EN 6
#define SDA 11
#define SCL 12

//expander addresses IOCON.BANK = 1
#define ADDR_EXP_1 0b0100000
#define ADDR_EXP_2 0x0100001
#define EXP_GPIOA 0x09 //value of pins 7-0
#define EXP_GPIOB 0x19
#define IODIR_A 0x00 //direction of pins 7-0
#define IODIR_B 0x10 // [0,1] -> [output,input]
#define IPOL_A //Polaridad del pin. Poner a 0 para ignorar
#define IPOL_B 
#define GPINT_A //enable interrupt. Poner a 0 para ign.
#define GPINT_B
#define IOCON_A 
#define IOCON_B


//temp sensor addresses
#define ADDR_TEMP 0b1001000

//pin addresses
#define P1_EN
#define P1_IN1 
#define P1_IN2
#define P2_EN
#define P2_IN1 
#define P2_IN2
#define P3_EN
#define P3_IN1 
#define P3_IN2
#define P4_EN
#define P4_IN1 
#define P4_IN2
#define P5_EN
#define P5_IN1
#define P5_IN2
#define W1_EN
#define W1_IN1 
#define W1_IN2
#define W2_EN
#define W2_IN1 
#define W2_IN2
#define R1_EN
#define R1_IN1 
#define R1_IN2


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