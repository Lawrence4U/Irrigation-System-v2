#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

typedef enum {
    TEMPERATURE = 0x01,
    LIGHT = 0x02,
} SensorType;

typedef struct{
    SensorType sens_type;
    float value;
}SensorData;

void processSerialData(SensorData* sens_data, char *rcv);
void prepareData(char* buffer, SensorType sensor_type, float sensor_value);

#endif