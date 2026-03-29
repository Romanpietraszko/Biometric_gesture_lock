#ifndef LOGIC_H
#define LOGIC_H

enum OperatingMode { MODE_AUTO, MODE_MANUAL };

struct SystemState {
  int angle;
  bool isLocked;
  OperatingMode mode;
  int securityEvents; // Prosta struktura danych (licznik)
};

class LockLogic {
public:
  SystemState state = {0, true, MODE_AUTO, 0};

  void update(int a, bool l) {
    state.angle = a;
    state.isLocked = l;
    if (l) state.securityEvents++;
  }
};
#endif