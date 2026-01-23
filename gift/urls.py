from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import GiftCardViewSet, GiftCardTransactionViewSet, GiftCardOnlinePaymentIntentViewSet, GiftCardStripeWebhookViewSet, GiftCardCheckoutViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'gift-cards', GiftCardViewSet, basename='gift-cards')
router.register(r'gift-card-transactions', GiftCardTransactionViewSet, basename='gift-card-transactions')
router.register(r'online-payment-intent', GiftCardOnlinePaymentIntentViewSet, basename='online-payment-intent')
router.register(r'gift-card-checkouts', GiftCardCheckoutViewSet, basename='gift-card-checkouts')

urlpatterns = [
    path(
        "gift-cards/stripe/webhook/",
        GiftCardStripeWebhookViewSet.as_view(),
        name="gift-card-stripe-webhook",
    ),
    path('', include(router.urls)),
]

