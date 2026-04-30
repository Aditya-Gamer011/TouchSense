import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

pyautogui.FAILSAFE = False

screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)

cv2.namedWindow("TouchSense", cv2.WINDOW_NORMAL)
cv2.resizeWindow("TouchSense", 1000, 700)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# ===== TUNED SETTINGS =====
alpha = 0.18              # smoother, less sensitive
MOVE_THRESHOLD = 8        # ignore tiny movements
DEADZONE = 3

PINCH_THRESHOLD = 0.045   # harder click
PINCH_RELEASE = 0.075

speed = 0.85              # slower cursor

curr_x, curr_y = 0, 0
dragging = False
last_click_time = 0

# ===== STATE =====
running = False

# ===== CALIBRATION =====
calibration_time = 3
start_time = 0
calibrated = False

min_x, max_x = 1e9, 0
min_y, max_y = 1e9, 0

# ===== HELPERS =====
def is_finger_up(tip, pip, lm):
    return lm[tip].y < lm[pip].y

def distance(p1, p2):
    return np.hypot(p1.x - p2.x, p1.y - p2.y)

def clamp(val, minv, maxv):
    return max(minv, min(val, maxv))

def is_inside_button(x, y, bx, by, bw, bh):
    return bx < x < bx + bw and by < y < by + bh

# ===== MOUSE CLICK HANDLER =====
def mouse_callback(event, x, y, flags, param):
    global running, start_time, calibrated, min_x, max_x, min_y, max_y

    if event == cv2.EVENT_LBUTTONDOWN:
        if is_inside_button(x, y, btn_x, btn_y, btn_w, btn_h):
            running = not running
            calibrated = False
            min_x, max_x = 1e9, 0
            min_y, max_y = 1e9, 0
            start_time = time.time()

cv2.setMouseCallback("TouchSense", mouse_callback)

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    # ===== UI CANVAS =====
    canvas = np.zeros((700, 1000, 3), dtype=np.uint8)
    canvas[:] = (30, 30, 30)

    # ===== TITLE =====
    cv2.putText(canvas, "TouchSense",
                (330, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.8, (255, 255, 255), 3)

    # ===== CAMERA FRAME =====
    cam_w, cam_h = 500, 350
    cam_x = 250
    cam_y = 120

    frame_resized = cv2.resize(img, (cam_w, cam_h))
    canvas[cam_y:cam_y+cam_h, cam_x:cam_x+cam_w] = frame_resized

    cv2.rectangle(canvas,
                  (cam_x-2, cam_y-2),
                  (cam_x+cam_w+2, cam_y+cam_h+2),
                  (100, 100, 100), 2)

    # ===== BUTTON =====
    btn_w, btn_h = 160, 60
    btn_x = 420
    btn_y = 520

    if running:
        btn_color = (0, 0, 200)
        btn_text = "STOP"
    else:
        btn_color = (0, 180, 0)
        btn_text = "START"

    cv2.rectangle(canvas,
                  (btn_x, btn_y),
                  (btn_x + btn_w, btn_y + btn_h),
                  btn_color, -1)

    cv2.putText(canvas, btn_text,
                (btn_x + 25, btn_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2)

    # ===== HAND TRACKING =====
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if running and result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            lm = hand.landmark
            current_time = time.time()

            index_up = is_finger_up(8, 6, lm)
            middle_up = is_finger_up(12, 10, lm)
            ring_up = is_finger_up(16, 14, lm)
            pinky_up = is_finger_up(20, 18, lm)

            thumb_tip_y = lm[4].y
            thumb_ip_y = lm[3].y
            thumb_up = thumb_tip_y < thumb_ip_y
            thumb_down = thumb_tip_y > thumb_ip_y

            x1 = int(lm[8].x * w)
            y1 = int(lm[8].y * h)

            # ===== CALIBRATION =====
            if not calibrated:
                min_x = min(min_x, x1)
                max_x = max(max_x, x1)
                min_y = min(min_y, y1)
                max_y = max(max_y, y1)

                if current_time - start_time > calibration_time:
                    padding = 20
                    min_x -= padding
                    max_x += padding
                    min_y -= padding
                    max_y += padding
                    calibrated = True

                cv2.putText(canvas, "Calibrating...",
                            (400, 500),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 255), 2)
                continue

            # ===== NORMALIZE =====
            x_norm = (x1 - min_x) / (max_x - min_x)
            y_norm = (y1 - min_y) / (max_y - min_y)

            x_norm = clamp(x_norm, 0, 1)
            y_norm = clamp(y_norm, 0, 1)

            x_target = x_norm * screen_w * speed
            y_target = y_norm * screen_h * speed

            # ===== ANTI-JITTER SMOOTHING =====
            if abs(x_target - curr_x) > MOVE_THRESHOLD:
                curr_x = alpha * x_target + (1 - alpha) * curr_x

            if abs(y_target - curr_y) > MOVE_THRESHOLD:
                curr_y = alpha * y_target + (1 - alpha) * curr_y

            pinch_dist = distance(lm[4], lm[8])

            try:
                # DRAG
                if pinch_dist < PINCH_THRESHOLD:
                    if not dragging:
                        pyautogui.mouseDown()
                        dragging = True
                elif pinch_dist > PINCH_RELEASE:
                    if dragging:
                        pyautogui.mouseUp()
                        dragging = False

                # MOVE
                if (index_up and middle_up) or dragging:
                    pyautogui.moveTo(curr_x, curr_y)

                # CLICK
                fist = not index_up and not middle_up and not ring_up and not pinky_up

                if fist and not dragging:
                    if current_time - last_click_time > 0.7:
                        pyautogui.click()
                        last_click_time = current_time

                # SCROLL
                if not index_up and not middle_up:
                    if thumb_up:
                        pyautogui.scroll(120)
                    elif thumb_down:
                        pyautogui.scroll(-120)

            except:
                pass

            mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

    # ===== UPDATE CAMERA FEED =====
    frame_resized = cv2.resize(img, (cam_w, cam_h))
    canvas[cam_y:cam_y+cam_h, cam_x:cam_x+cam_w] = frame_resized

    cv2.imshow("TouchSense", canvas)

    key = cv2.waitKey(1)
    if key == 27 or key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()