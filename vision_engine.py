import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

class VisionEngine:
    def __init__(self):
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def get_landmarks(self, frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        return self.detector.detect_for_video(mp_image, int(time.time() * 1000))