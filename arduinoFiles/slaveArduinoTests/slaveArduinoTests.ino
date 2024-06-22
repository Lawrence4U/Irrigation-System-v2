#include <serialProtocol.h>


void setup(){

    Serial.begin(115200);
    while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
    }
    Serial.println("Ready\n");

}

void loop(){
  char buffer[8];
  float sensor_value = 27.35;
  // SensorType sensor_type = TEMPERATURE;
  prepareData(buffer, LIGHT, sensor_value);
  SensorData data;
  processSerialData(&data, buffer);

  Serial.print(data.sens_type);
  Serial.print("->");
  Serial.println(data.value);
  delay(1000);
}