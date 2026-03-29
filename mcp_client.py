import serial
import json
import time

class MCPClient:
    def __init__(self, port='/dev/ttyACM0', baud=115200):
        """Inicjalizacja połączenia z Arduino (Server MCP)"""
        try:
            # timeout=0 sprawia, że operacje są nieblokujące - ważne dla płynności GUI
            self.ser = serial.Serial(port, baud, timeout=0)
            self.last_send_time = 0
            print(f"Polaczono z MCP Server na porcie: {port}")
        except Exception as e:
            self.ser = None
            print(f"BLAD: Nie mozna otworzyc portu {port}. Sprawdz uprawnienia (chmod 666).")

    def send_state(self, angle, locked):
        """Wysyła aktualny stan rygla (kąt i blokada)"""
        now = time.time()
        # Limit wysyłania: max 20 razy na sekundę (co 50ms), by nie zapchać bufora
        if self.ser and (now - self.last_send_time > 0.05):
            payload = {
                "command": "set_state",
                "angle": int(angle),
                "locked": bool(locked)
            }
            self._transmit(payload)
            self.last_send_time = now

    def send_mode(self, mode_name):
        """Zmienia tryb pracy systemu: 'auto' lub 'manual'"""
        if self.ser:
            payload = {
                "command": "set_mode",
                "value": mode_name.lower() # auto / manual
            }
            self._transmit(payload)
            print(f"Zmieniono tryb na: {mode_name}")

    def request_status(self):
        """Zapytanie o aktualny status urządzenia"""
        if self.ser:
            payload = {"command": "status"}
            self._transmit(payload)

    def _transmit(self, data):
        """Wysyła sformatowany JSON z terminatorem nowej linii"""
        try:
            json_string = json.dumps(data) + "\n"
            self.ser.write(json_string.encode('utf-8'))
        except Exception as e:
            print(f"Blad transmisji: {e}")

    def close(self):
        """Zamyka bezpiecznie port szeregowy"""
        if self.ser:
            self.ser.close()