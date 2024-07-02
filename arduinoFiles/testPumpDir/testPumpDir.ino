#include <Adafruit_MCP23X17.h>
#include <Adafruit_MCP23XXX.h>

#define ADDR_EXP_1 0b0100000
#define ADDR_EXP_2 0b0100001

//pin addresses of I/O expander EXP_1
//GPIOB
#define P1_EN   0 + 8 //GPIOA i 0-7 and B is 8-15
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

Adafruit_MCP23X17 expander1;

void setup(){
    Serial.begin(115200);
    while (!Serial);
    Serial.println("MCP23xxx Blink Test!");

    if (!expander1.begin_I2C(ADDR_EXP_1)) {
        Serial.println("Error starting expander1.");
        while (1);
    }
    expander1.pinMode(W2_EN, OUTPUT);
    expander1.pinMode(W2_IN1, OUTPUT);
    expander1.pinMode(P1_IN2, OUTPUT);
    expander1.digitalWrite(W2_EN, HIGH);
    
    Serial.println("Looping...");
}

void loop(){
    Serial.println("From pin " + String(P1_IN1) + "to " + String(P1_IN2));
    expander1.digitalWrite(W2_IN1, HIGH);
    expander1.digitalWrite(W2_IN2, LOW);
    delay(5000);
    Serial.println("Reversed");
    expander1.digitalWrite(W2_IN1, LOW);
    expander1.digitalWrite(W2_IN2, HIGH);
    delay(5000);
}