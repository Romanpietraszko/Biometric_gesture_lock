import cv2
import numpy as np
import time
from vision_engine import VisionEngine
from mcp_client import MCPClient

# --- KONFIGURACJA ---
mcp = MCPClient(port='/dev/ttyACM0') 
vision = VisionEngine()
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Stany logiczne
current_mode = "AUTO" 
lock_angle = 0
is_locked = True
master_authorized = False
show_closed_text = False

# Maszyna stanów sekwencji
open_seq_start = 0  # Czas wykrycia pierwszego gestu otwierania
close_seq_start = 0 # Czas wykrycia pierwszego gestu zamykania

def draw_mechanical_ui(frame, angle, locked, gesture, authorized, show_closed):
    h, w, _ = frame.shape
    cx, cy = w - 150, h - 220 
    color = (0, 0, 255) if locked else (0, 255, 0)
    
    # 1. Tarcza Zamka
    cv2.circle(frame, (cx, cy), 80, (30, 30, 30), -1)
    cv2.circle(frame, (cx, cy), 80, (150, 150, 150), 2)
    
    # Ikona kłódki
    cv2.rectangle(frame, (cx-25, cy-10), (cx+25, cy+30), color, -1)
    if locked:
        cv2.circle(frame, (cx, cy-10), 18, color, 3) 
        if show_closed:
            cv2.putText(frame, "CLOSED", (cx-26, cy+15), cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)
    else:
        cv2.ellipse(frame, (cx+15, cy-15), (18, 18), 0, 180, 360, color, 3)
        if authorized:
            cv2.putText(frame, "OPEN", (cx-22, cy+15), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (255, 255, 255), 2)

    # 2. Rygiel (Digital Twin)
    rx, ry = w - 280, h - 80
    cv2.rectangle(frame, (rx, ry), (rx + 220, ry + 25), (40, 40, 40), -1)
    cv2.rectangle(frame, (rx, ry), (rx + 220, ry + 25), (120, 120, 120), 2)
    
    bolt_pos = int(np.interp(0 if locked else angle, [0, 180], [0, 175]))
    cv2.rectangle(frame, (rx + bolt_pos, ry - 15), (rx + bolt_pos + 45, ry + 40), color, -1)
    cv2.rectangle(frame, (rx + bolt_pos, ry - 15), (rx + bolt_pos + 45, ry + 40), (255, 255, 255), 2)
    cv2.putText(frame, "SERVO BOLT", (rx + 5, ry + 20), 0, 0.4, (255, 255, 255), 1)

    # 3. Status
    cv2.rectangle(frame, (0, 0), (350, 110), (25, 25, 25), -1)
    cv2.putText(frame, f"MODE: {current_mode} | GEST: {gesture}", (20, 35), 0, 0.5, (255, 255, 0), 1)
    status_txt = "SECURED" if locked else "ACCESS GRANTED"
    cv2.putText(frame, status_txt, (20, 85), 0, 0.8, color, 2)

def check_gestures(lms):
    fingers = []
    tips = [8, 12, 16, 20]
    bases = [5, 9, 13, 17]
    for t, b in zip(tips, bases):
        fingers.append(lms[t].y < lms[b].y)

    if all(fingers): return "OPEN PALM"
    if fingers[0] and fingers[1] and not fingers[2] and not fingers[3]: return "PEACE"
    if fingers[0] and not fingers[1] and not fingers[2] and fingers[3]: return "ROCK"
    if not any(fingers): return "FIST"
    return "NONE"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    
    res = vision.get_landmarks(frame)
    detected_gesture = "NONE"
    now = time.time()
    
    if res.hand_landmarks:
        lms = res.hand_landmarks[0]
        detected_gesture = check_gestures(lms)
        
        # --- LOGIKA SEKWENCJI ---
        
        # 1. Start sekwencji Otwierania (PEACE)
        if detected_gesture == "PEACE" and not master_authorized:
            open_seq_start = now
        # 2. Potwierdzenie Otwierania (ROCK po PEACE w ciągu 2s)
        elif detected_gesture == "ROCK" and (now - open_seq_start < 2.0):
            master_authorized = True
            show_closed_text = False
            open_seq_start = 0

        # 3. Start sekwencji Zamykania (ROCK)
        if detected_gesture == "ROCK" and master_authorized:
            close_seq_start = now
        # 4. Potwierdzenie Zamykania (PEACE po ROCK w ciągu 2s)
        elif detected_gesture == "PEACE" and (now - close_seq_start < 2.0):
            master_authorized = False
            show_closed_text = True
            close_seq_start = 0
            is_locked = True

        # 5. Resetowanie wszystkiego (FIST)
        if detected_gesture == "FIST":
            master_authorized = False
            show_closed_text = False
            open_seq_start = 0
            close_seq_start = 0
            is_locked = True

        # LOGIKA RYGLA
        if master_authorized or detected_gesture == "OPEN PALM":
            is_locked = False
            lock_angle = int(lms[0].x * 180)
        else:
            is_locked = True
            lock_angle = 0
    else:
        # Brak dłoni - zamykamy jeśli nie ma Mastera
        if not master_authorized:
            is_locked = True
            lock_angle = 0
            show_closed_text = False

    mcp.send_state(lock_angle, is_locked)
    draw_mechanical_ui(frame, lock_angle, is_locked, detected_gesture, master_authorized, show_closed_text)
    
    cv2.imshow("Smart Lock MCP", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()