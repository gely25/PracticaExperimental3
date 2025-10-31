from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .camera import camera_singleton as camera
from .detectors.face import FaceDetector
from .models import Attendance

import cv2
import time
import os
import numpy as np


# =======================================================
# INSTANCIAS Y VARIABLES GLOBALES
# =======================================================
face_detector = FaceDetector()
LAST_FACE_COUNT = 0  # para los indicadores de la interfaz


# =======================================================
# VISTA PRINCIPAL
# =======================================================
def index_view(request):
    """Carga la página principal del sistema."""
    return render(request, 'vision/index.html')


# =======================================================
# STREAM DE VIDEO CON DETECCIÓN
# =======================================================
def gen_frames():
    """Genera los frames del stream con detección de rostros."""
    global LAST_FACE_COUNT
    prev_t = time.time()

    while True:
        # Si la cámara está apagada → frame negro
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

        # Detección de rostros
        faces = face_detector.detect(frame)
        LAST_FACE_COUNT = len(faces)

        # Dibujar rectángulos
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Codificar a JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


def video_feed(request):
    """Devuelve el stream MJPEG."""
    return StreamingHttpResponse(gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame')


# =======================================================
# REGISTRO DE ASISTENCIA
# =======================================================
@csrf_exempt
@require_POST
def mark_attendance(request):
    """Guarda la asistencia con el nombre y captura del frame actual."""
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "msg": "Por favor ingresa tu nombre."}, status=400)

    # Obtener frame actual
    ok, frame = camera.read()
    if not ok or frame is None:
        return JsonResponse({"ok": False, "msg": "No se pudo obtener la imagen."}, status=500)

    # Detectar rostros
    faces = face_detector.detect(frame)

    # Crear carpeta media/attendance
    os.makedirs(os.path.join(settings.MEDIA_ROOT, "attendance"), exist_ok=True)

    # Guardar imagen
    filename = f"{int(time.time())}_{name.replace(' ', '_')}.jpg"
    file_path = os.path.join(settings.MEDIA_ROOT, "attendance", filename)
    rel_path = f"attendance/{filename}"
    cv2.imwrite(file_path, frame)

    # Guardar registro en la BD
    Attendance.objects.create(
        name=name,
        photo_path=rel_path,
        faces_detected=len(faces)
    )

    return JsonResponse({
        "ok": True,
        "msg": f"Asistencia registrada para {name} (rostros: {len(faces)})",
        "photo": settings.MEDIA_URL + rel_path
    })


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


def stats(request):
    """Indicadores básicos para la interfaz (cámara y rostros detectados)."""
    return JsonResponse({
        "camera": "on" if camera.is_open() else "off",
        "faces": LAST_FACE_COUNT
    })


# =======================================================
# REPORTE DE ASISTENCIAS
# =======================================================
def report_view(request):
    """Muestra la tabla con todas las asistencias registradas."""
    records = Attendance.objects.all().order_by('-timestamp')
    return render(request, 'vision/report.html', {'records': records})
