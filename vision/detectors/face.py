import cv2

class FaceDetector:
    def __init__(self):
        # Cargamos el clasificador Haar Cascade incluido en OpenCV
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect(self, frame_bgr):
        """Detecta rostros en el frame (imagen en color BGR)"""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
        return faces  # devuelve una lista de (x, y, w, h)
