from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppointmentViewSet,
    AppointmentServiceViewSet,
    BusinessBookingViewSet
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'appointment-services', AppointmentServiceViewSet, basename='appointment-service')
router.register(r'business-booking', BusinessBookingViewSet, basename='business-booking')

urlpatterns = [
    path('', include(router.urls)),
]
