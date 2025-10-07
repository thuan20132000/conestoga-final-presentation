from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppointmentViewSet, AppointmentStatusViewSet,
    AppointmentReminderViewSet, AppointmentConflictViewSet, AppointmentServiceViewSet
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'statuses', AppointmentStatusViewSet, basename='appointmentstatus')
router.register(r'reminders', AppointmentReminderViewSet, basename='appointmentreminder')
router.register(r'conflicts', AppointmentConflictViewSet, basename='appointmentconflict')
router.register(r'appointment-services', AppointmentServiceViewSet, basename='appointmentservice')

urlpatterns = [
    path('', include(router.urls)),
]
