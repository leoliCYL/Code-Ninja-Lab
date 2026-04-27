import cv2
import mediapipe as mp
import time
import numpy as np
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from queue import Queue
from pymongo import MongoClient


def is_ok_sign(hand_lms):
    if not hand_lms: return False
    dx, dy = hand_lms[4].x - hand_lms[8].x, hand_lms[4].y - hand_lms[8].y
    distance = (dx**2 + dy**2)**0.5
    others_up = all(hand_lms[tip].y < hand_lms[tip - 2].y for tip in [12, 16, 20])
    return distance < 0.05 and others_up


class PasswordApp:
    def __init__(self):
        mongodb_uri = os.getenv('VITE_MONGO_URI')
        if mongodb_uri is None:
            raise Exception('Environment variable VITE_MONGO_URI must be set')
        self.client = MongoClient(mongodb_uri)

        self.event_queue = Queue()

        self.entered_password = []
        self.app_state = ''
        self.current_gameId = ''
        self.set_app_state("LOCKED")
        self.last_finger_count = -1
        self.start_time = 0
        self.HOLD_TIME = 1.5
        self.username = ""

        self.del_btn = {'x1': 0.88, 'y1': 0.05, 'x2': 0.97, 'y2': 0.12, 'color': (0, 0, 255)}
        self.ent_btn = {'x1': 0.77, 'y1': 0.05, 'x2': 0.86, 'y2': 0.12, 'color': (0, 255, 0)}

        self.delete_cooldown = 0
        self.enter_hover_start = 0
        self.reset_hover_start = 0
        self.status_msg = "Show first digit"

        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=2, min_hand_detection_confidence=0.4)
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.capture = cv2.VideoCapture(0)

    def close(self):
        self.capture.release()

    def find_user_by_pin(self, pin):
        db = self.client.test
        user = db.currentusers.find_one({"pin": str(pin)})
        return user

    def set_app_state(self, state, gameId=""):
        if state == self.app_state:
            return
        self.app_state = state
        self.current_gameId = gameId
        self.event_queue.put({'state': state, 'gameId': gameId})

    def enter_password(self):
        pin = "".join(map(str, self.entered_password))
        user = self.find_user_by_pin(pin)
        if user is not None:
            self.username = user['username']
            self.set_app_state("GRANTED", user.get('gameId', ''))
        else:
            self.set_app_state("DENIED")

    def get_frame(self):
        success, frame = self.capture.read()
        if not success:
            return None
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # --- STATE: RESULTS PAGE ---
        if self.app_state != "LOCKED":
            page = np.zeros((h, w, 3), dtype=np.uint8)
            t = time.time()
            pulse = int(25 * np.sin(t * 5))
            color = (0, 255, 0) if self.app_state == "GRANTED" else (0, 0, 255)
            txt = "ACCESS UNLOCKED" if self.app_state == "GRANTED" else "ACCESS DENIED"
            cv2.putText(page, txt, (w//2 - 280, h//2 - 50), 1, 3, color, 4)
            cv2.circle(page, (w//2, h//2 + 120), 70 + pulse, color, 2)
            cv2.putText(page, "Hold OK for 0.5s to Reset", (w//2 - 180, h - 50), 1, 1, (255, 255, 255), 1)
            if self.app_state == "GRANTED":
                cv2.putText(page, f"Welcome {self.username}", (w // 2 - 280, h // 2), 1, 3, color, 4)

            rgb_p = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res_p = self.detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_p))
            if res_p and res_p.hand_landmarks:
                for lms in res_p.hand_landmarks:
                    if is_ok_sign(lms):
                        if self.reset_hover_start == 0: self.reset_hover_start = time.time()
                        if time.time() - self.reset_hover_start > 0.5:
                            self.entered_password = []
                            self.set_app_state("LOCKED")
                    else: self.reset_hover_start = 0

            return page

        # --- LOCKED: detection + drawing ---
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame))

        if len(self.entered_password) > 0:
            cv2.rectangle(frame, (int(self.del_btn['x1']*w), int(self.del_btn['y1']*h)), (int(self.del_btn['x2']*w), int(self.del_btn['y2']*h)), self.del_btn['color'], -1)
            cv2.putText(frame, "DEL", (int(self.del_btn['x1']*w)+8, int(self.del_btn['y1']*h)+32), 0, 0.6, (255, 255, 255), 2)

        if len(self.entered_password) == 4:
            cv2.rectangle(frame, (int(self.ent_btn['x1']*w), int(self.ent_btn['y1']*h)), (int(self.ent_btn['x2']*w), int(self.ent_btn['y2']*h)), self.ent_btn['color'], -1)
            cv2.putText(frame, "ENT", (int(self.ent_btn['x1']*w)+8, int(self.ent_btn['y1']*h)+32), 0, 0.6, (0, 0, 0), 2)

        current_frame_fingers = 0

        if result and result.hand_landmarks:
            for hand_lms in result.hand_landmarks:
                ix, iy = hand_lms[8].x, hand_lms[8].y

                if is_ok_sign(hand_lms):
                    if self.reset_hover_start == 0: self.reset_hover_start = time.time()
                    if time.time() - self.reset_hover_start > 0.5:
                        self.entered_password = []
                        self.status_msg = "System Reset"
                    break
                else: self.reset_hover_start = 0

                if len(self.entered_password) > 0 and self.del_btn['x1'] < ix < self.del_btn['x2'] and self.del_btn['y1'] < iy < self.del_btn['y2']:
                    self.del_btn['color'] = (0, 255, 255)
                    if time.time() > self.delete_cooldown:
                        self.entered_password.pop()
                        self.delete_cooldown = time.time() + 1.2
                else: self.del_btn['color'] = (0, 0, 255)

                if len(self.entered_password) == 4 and self.ent_btn['x1'] < ix < self.ent_btn['x2'] and self.ent_btn['y1'] < iy < self.ent_btn['y2']:
                    self.ent_btn['color'] = (255, 255, 255)
                    if self.enter_hover_start == 0: self.enter_hover_start = time.time()
                    if time.time() - self.enter_hover_start > 1.2:
                        self.enter_password()
                else:
                    self.ent_btn['color'] = (0, 255, 0)
                    if len(self.entered_password) == 4: self.enter_hover_start = 0

                if len(self.entered_password) < 4:
                    up_count = sum(1 for tip in [8, 12, 16, 20] if hand_lms[tip].y < hand_lms[tip - 2].y - 0.05)
                    t_dist = ((hand_lms[4].x - hand_lms[5].x)**2 + (hand_lms[4].y - hand_lms[5].y)**2)**0.5
                    if t_dist > 0.12: up_count += 1
                    current_frame_fingers += up_count

                for lm in hand_lms:
                    cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 3, (0, 255, 0), -1)

        if current_frame_fingers > 9: current_frame_fingers = 9

        if len(self.entered_password) < 4:
            if current_frame_fingers > 0 and current_frame_fingers == self.last_finger_count:
                elapsed = time.time() - self.start_time
                self.status_msg = f"Holding {current_frame_fingers}... {max(0, self.HOLD_TIME - elapsed):.1f}s"
                if elapsed >= self.HOLD_TIME:
                    self.entered_password.append(current_frame_fingers)
                    self.last_finger_count = -1
            else:
                self.last_finger_count, self.start_time = current_frame_fingers, time.time()
                self.status_msg = f"Live: {current_frame_fingers} | Digit {len(self.entered_password) + 1}"
        else:
            self.status_msg = "Confirm Password: Hover 'ENT'"

        pass_str = " ".join(map(str, self.entered_password)) + " _ " * (4 - len(self.entered_password))
        cv2.rectangle(frame, (0, h-70), (w, h), (0,0,0), -1)
        cv2.putText(frame, f"Pass: {pass_str}", (20, h-25), 1, 1.8, (255, 255, 255), 2)
        cv2.putText(frame, self.status_msg, (20, 45), 1, 1.5, (0, 255, 255), 2)

        return frame
