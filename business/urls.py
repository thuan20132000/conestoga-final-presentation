from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessTypeViewSet, BusinessViewSet, OperatingHoursViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'business-types', BusinessTypeViewSet, basename='business-type')
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'operating-hours', OperatingHoursViewSet, basename='operating-hours')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
