#include <Servo.h> 
#include <ArduinoJson.h>
#include "Logic.h"
//Server MPC
Servo myservo;
LockLogic logic;

void setup() {
  Serial.begin(115200);
  myservo.attach(9);
  myservo.write(0);
}

void loop() {
  if (Serial.available() > 0) {
    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, Serial) == DeserializationError::Ok) {
      String cmd = doc["command"];
      
      if (cmd == "set_state") {
        logic.update(doc["angle"], doc["locked"]);
        // Fizyczna blokada: jeśli locked, serwo zawsze na 0
        myservo.write(logic.state.isLocked ? 0 : logic.state.angle);
      } 
      else if (cmd == "set_mode") {
        String m = doc["value"];
        logic.state.mode = (m == "auto") ? MODE_AUTO : MODE_MANUAL;
      }
      // Automatyczny raport po każdej zmianie (wymóg statusu)
      sendReport();
    }
  }
}

void sendReport() {
  StaticJsonDocument<200> res;
  res["status"] = logic.state.isLocked ? "LOCKED" : "UNLOCKED";
  res["mode"] = (logic.state.mode == MODE_AUTO) ? "auto" : "manual";
  res["events"] = logic.state.securityEvents;
  serializeJson(res, Serial);
  Serial.println();
}