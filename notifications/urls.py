from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, PushDeviceViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"push-devices", PushDeviceViewSet, basename="pushdevice")

urlpatterns = [
    path("", include(router.urls)),
]
