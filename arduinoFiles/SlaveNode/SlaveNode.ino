#include <Adafruit_VEML7700.h>
#include <Wire.h>
#include <serialProtocol.h>
#include <Temperature_LM75_Derived.h>

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

Generic_LM75 temperature(TMP75_ADDR);
Adafruit_VEML7700 veml = Adafruit_VEML7700();

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }

  if (!veml.begin()) {
    Serial.println("Sensor not found");
    while (1);
  }

  Serial.println("Ready\n");

  Wire.begin();
}

char sendBuffer[8];
float temp_data=0;
float light_data=0;

void loop() {

  //Read sensors
  temp_data = temperature.readTemperatureC();
  light_data = veml.readLux(VEML_LUX_AUTO);

  //send data
  prepareData(sendBuffer, TEMPERATURE, temp_data);
  Serial.println(sendBuffer);
  prepareData(sendBuffer, LIGHT, light_data);
  Serial.println(sendBuffer);
  delay(1000);

}
