#ifndef HARDWARE_H
#define HARDWARE_H
#include <Servo.h>
#include "Config.h"

class Hardware {
    Servo myservo;
public:
    void init() { myservo.attach(SERVO_PIN); myservo.write(0); }
    void move(int a) { myservo.write(constrain(a, 0, 180)); }
};
#endif