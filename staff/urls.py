from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffViewSet, StaffWorkingHoursViewSet, StaffOffDayViewSet
# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'working-hours', StaffWorkingHoursViewSet, basename='staff-working-hours')
router.register(r'off-days', StaffOffDayViewSet, basename='staff-off-days')
# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
