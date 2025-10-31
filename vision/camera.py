import cv2
import threading

class Camera:
    def __init__(self, src=0, width=640, height=480):
        self.src = src
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.lock = threading.Lock()

    def is_open(self):
        return self.cap is not None and self.cap.isOpened()

    def open(self):
        with self.lock:
            if not self.is_open():
                self.cap = cv2.VideoCapture(self.src)

    def read(self):
        with self.lock:
            if not self.is_open():
                return False, None
            return self.cap.read()

    def release(self):
        with self.lock:
            if self.cap and self.cap.isOpened():
                self.cap.release()

camera_singleton = Camera()


