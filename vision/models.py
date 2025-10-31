from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    """
    Registro de asistencia:
    - name: nombre del participante
    - timestamp: fecha y hora del registro
    - photo_path: archivo con la captura
    - faces_detected: cantidad de rostros detectados
    """
    name = models.CharField(max_length=120)
    timestamp = models.DateTimeField(default=timezone.now)
    faces_detected = models.PositiveIntegerField(default=0)
    photo_path = models.ImageField(upload_to='photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.timestamp:%Y-%m-%d %H:%M:%S}"
