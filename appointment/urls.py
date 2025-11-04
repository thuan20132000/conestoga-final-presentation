from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppointmentViewSet,
    AppointmentServiceViewSet
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'appointment-services', AppointmentServiceViewSet, basename='appointment-service')

urlpatterns = [
    path('', include(router.urls)),
]
