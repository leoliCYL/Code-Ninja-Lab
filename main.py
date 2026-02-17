import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def main():
    # 1. Setup MediaPipe Tasks
    model_path = 'hand_landmarker.task'
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options, 
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    print("Camera started. Tracking up to 10 fingers. Press 'q' to quit.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success: continue

        frame = cv2.flip(frame, 1) # Mirroring for natural feel
        h, w, _ = frame.shape
        
        # Convert to MediaPipe image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Perform detection
        result = detector.detect(mp_image)
        total_fingers = 0

        # Check if landmarks exist to avoid crashes
        if result and result.hand_landmarks:
            for i, hand_lms in enumerate(result.hand_landmarks):
                
                # --- SAFE DRAWING ---
                for lm in hand_lms:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

                # --- SAFE HANDEDNESS & COUNTING ---
                try:
                    # New API uses 'handedness' instead of 'hand_handedness'
                    handedness_list = getattr(result, 'handedness', None)
                    if handedness_list and i < len(handedness_list):
                        label = handedness_list[i][0].category_name
                    else:
                        label = "Unknown"

                    # 4 Fingers (Y-axis logic)
                    tips = [8, 12, 16, 20]
                    up_count = 0
                    for tip in tips:
                        if hand_lms[tip].y < hand_lms[tip - 2].y:
                            up_count += 1
                    
                    # Thumb Logic (Mirror-Aware)
                    if label == "Right":
                        if hand_lms[4].x > hand_lms[3].x: up_count += 1
                    else:
                        if hand_lms[4].x < hand_lms[3].x: up_count += 1
                    
                    total_fingers += up_count
                except Exception:
                    continue # Skip current hand if logic fails, but keep app running

        # Display result
        cv2.putText(frame, f'Fingers: {total_fingers}', (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.imshow("Code-Ninja-Lab Safe Tracker", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)

if __name__ == "__main__":
    main()