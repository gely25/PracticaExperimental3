from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .camera import camera_singleton as camera
from .detectors.face import FaceDetector
import cv2
import time
import os
import numpy as np

# =======================================================
# INSTANCIAS Y VARIABLES GLOBALES
# =======================================================
face_detector = FaceDetector()
LAST_PERSON_COUNT = 0  # almacena el conteo actual para mostrar en interfaz


# =======================================================
# VISTA PRINCIPAL
# =======================================================
def index_view(request):
    """Carga la página principal del sistema de conteo."""
    return render(request, 'vision/index.html')


# =======================================================
# STREAM DE VIDEO CON DETECCIÓN
# =======================================================
def gen_frames():
    """Genera los frames del stream con detección de personas (rostros)."""
    global LAST_PERSON_COUNT

    while True:
        # Si la cámara está apagada → mostrar pantalla negra
        if not camera.is_open():
            frame = np.zeros((480, 640, 3), dtype='uint8')
            cv2.putText(frame, "Cámara apagada", (160, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.2)
            continue

        ok, frame = camera.read()
        if not ok or frame is None:
            time.sleep(0.05)
            continue

        # Detección de rostros (personas)
        persons = face_detector.detect(frame)
        LAST_PERSON_COUNT = len(persons)

        # Dibujar rectángulos y contador
        for (x, y, w, h) in persons:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(frame, f"Personas detectadas: {LAST_PERSON_COUNT}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # Codificar frame a JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


def video_feed(request):
    """Devuelve el stream MJPEG al navegador."""
    return StreamingHttpResponse(gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame')


# =======================================================
# CONTROL DE CÁMARA
# =======================================================
@csrf_exempt
def toggle_camera(request):
    """Activa o desactiva físicamente la cámara de OpenCV."""
    action = request.GET.get("action")
    if action == "on":
        camera.open()
        return JsonResponse({"ok": True, "status": "on"})
    elif action == "off":
        camera.release()
        return JsonResponse({"ok": True, "status": "off"})
    return JsonResponse({"ok": False, "msg": "Acción inválida"}, status=400)


# =======================================================
# ESTADÍSTICAS PARA LA INTERFAZ
# =======================================================
def stats(request):
    """Devuelve el estado actual (cámara y cantidad de personas detectadas)."""
    return JsonResponse({
        "camera": "on" if camera.is_open() else "off",
        "faces": LAST_PERSON_COUNT
    })
