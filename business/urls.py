from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessTypeViewSet,
    BusinessViewSet,
    OperatingHoursViewSet,
    BusinessSettingsViewSet,
    BusinessOnlineBookingViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'business', BusinessViewSet, basename='business')
router.register(r'business-type', BusinessTypeViewSet, basename='business-type')
router.register(r'operating-hours', OperatingHoursViewSet, basename='operating-hours')
router.register(r'business-settings', BusinessSettingsViewSet, basename='business-settings')
router.register(r'business-online-booking', BusinessOnlineBookingViewSet, basename='business-online-booking')
# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
