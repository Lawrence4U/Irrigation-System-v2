#include "serialProtocol.h"
#include <Arduino.h>


void prepareData(char* buffer, SensorType sensor_type, float sensor_value){
    sprintf(buffer, "%02d%05d", sensor_type, (int)(sensor_value*100));
}

void processSerialData(SensorData* sens_data, char *rcv){
    char type[3];
    strncpy(type, rcv, 2);
    SensorType s_type = (SensorType)atoi(type);
    type[2] = '\0';
    
    char numbers[4];
    char decimals[3];
    strncpy(numbers, rcv + 2, 3);
    numbers[3] = '\0';
    strncpy(decimals, rcv + 5, 2);
    decimals[2] = '\0';
    
    float float_value = atoi(numbers) + (float)atoi(decimals) / 100.0f;
    sens_data->sens_type = s_type;
    sens_data->value = float_value;
    
}

