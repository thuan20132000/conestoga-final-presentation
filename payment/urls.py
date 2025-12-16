from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    POSPaymentViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'payments', PaymentViewSet)
router.register(r'pos-payments', POSPaymentViewSet, basename='pos-payments')

urlpatterns = [
    path('', include(router.urls)),
]
