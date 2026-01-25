from __future__ import annotations

from typing import Any, Optional

import stripe
from django.conf import settings

from payment.models import PaymentGateway, GatewayTypeType

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

STRIPE_APPLICATION_FEE_PERCENTAGE = 0.05

class StripeService:
    def __init__(self, business_id: Optional[int] = None) -> None:
        self.business_id = business_id
        self.api_key, self.webhook_secret, self.merchant_id= self._resolve_keys(business_id)
        if not self.api_key:
            raise ValueError("Stripe API key is not configured")
        stripe.api_key = self.api_key

    def _resolve_keys(self, business_id: Optional[int]) -> tuple[str, str]:
        merchant_id = None
        if business_id:
            gateway = (
                PaymentGateway.objects.filter( 
                    business_id=business_id,
                    gateway_type=GatewayTypeType.STRIPE,
                    is_active=True,
                )
                .order_by("-is_default", "name")
                .first()
            )
            if gateway and gateway.is_active == True:
                merchant_id = gateway.merchant_id
        return settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET, merchant_id

    def _calculate_application_fee_amount(self, amount_cents: int) -> int:
        return int(amount_cents * STRIPE_APPLICATION_FEE_PERCENTAGE)
    
    def create_payment_intent(
        self,
        amount_cents: int,
        currency: str,
        metadata: dict[str, str],
        description: str,
    ) -> Any:
        return stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata,
            description=description,
            automatic_payment_methods={"enabled": True},
        )

    def construct_event(self, payload: bytes, signature: str) -> Any:
        if not self.webhook_secret:
            raise ValueError("Stripe webhook secret is not configured")
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=self.webhook_secret,
        )

    def retrieve_payment_intent(self, payment_intent_id: str) -> stripe.PaymentIntent:
        return stripe.PaymentIntent.retrieve(payment_intent_id)

    def retrieve_checkout_session(self, checkout_session_id: str) -> stripe.checkout.Session:
        try:
            response = stripe.checkout.Session.retrieve(checkout_session_id)
            return response
        except Exception as e:
            logger.error("error retrieving Stripe checkout session:: %s", e)
            raise e

    def create_checkout_session(
        self,
        amount_cents: int,
        currency: str,
        metadata: dict[str, str],
        description: str,
        success_url: str,
        cancel_url: str,
    ) -> stripe.Checkout.Session:
        try:
            application_fee_amount = self._calculate_application_fee_amount(amount_cents)
            payment_intent_data = {
                "metadata": metadata,
            }
            if self.merchant_id:
                payment_intent_data["application_fee_amount"] = application_fee_amount
                payment_intent_data["transfer_data"] = {
                    "destination": self.merchant_id,
                }
            
            session = stripe.checkout.Session.create(
                line_items=[{
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": description,
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                payment_intent_data=payment_intent_data,
            )
            return session
        except Exception as e:
            logger.error("error creating Stripe checkout session:: %s", e)
            raise e