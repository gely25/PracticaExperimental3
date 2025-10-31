from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("name", "timestamp", "faces_detected", "photo_path")
    list_filter = ("timestamp",)