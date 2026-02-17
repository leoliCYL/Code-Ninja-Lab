import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def main():
    # 1. Initialize the Landmarker
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
    detector = vision.HandLandmarker.create_from_options(options)

    # 2. Try to open the camera (0 is usually the built-in FaceTime HD camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera. Check privacy settings.")
        return

    print("Camera started. Press 'q' to quit.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        frame = cv2.flip(frame, 1) # Mirror for natural feel
        
        # 3. Process the frame
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = detector.detect(mp_image)

        total_fingers = 0
        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                # Finger counting logic
                tips = [8, 12, 16, 20]
                up_count = sum(1 for tip in tips if landmarks[tip].y < landmarks[tip - 2].y)
                
                # Thumb logic
                if landmarks[4].x > landmarks[3].x: up_count += 1
                total_fingers = up_count

        # 4. Display Output
        cv2.putText(frame, f'Fingers: {total_fingers}', (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.imshow("Code-Ninja-Lab Tracker", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()