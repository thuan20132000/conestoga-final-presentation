from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffTurnViewSet

router = DefaultRouter()
router.register(r'staff-turns', StaffTurnViewSet, basename='staff-turns')

urlpatterns = [
    path('', include(router.urls)),
]
