from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('events/', views.calendar_events_json, name='calendar_events_json'),
]
