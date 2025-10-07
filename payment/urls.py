from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentMethodViewSet, PaymentStatusViewSet, PaymentGatewayViewSet,
    PaymentViewSet, PaymentSplitViewSet, RefundViewSet, PaymentTransactionViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet)
router.register(r'payment-statuses', PaymentStatusViewSet)
router.register(r'payment-gateways', PaymentGatewayViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'payment-splits', PaymentSplitViewSet)
router.register(r'refunds', RefundViewSet)
router.register(r'payment-transactions', PaymentTransactionViewSet)

app_name = 'payment'

urlpatterns = [
    path('', include(router.urls)),
]
