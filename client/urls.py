from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ClientPreferenceViewSet, ClientHistoryViewSet

app_name = 'client'

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'preferences', ClientPreferenceViewSet, basename='client-preference')
router.register(r'history', ClientHistoryViewSet, basename='client-history')

urlpatterns = [
    path('', include(router.urls)),
]
