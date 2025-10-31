from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('toggle_camera/', views.toggle_camera, name='toggle_camera'),
    path('stats/', views.stats, name='stats'),
    path('report/', views.report_view, name='report'),  


]


