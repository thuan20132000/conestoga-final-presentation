from __future__ import annotations

from typing import Any, Optional

import stripe
from django.conf import settings

from payment.models import PaymentGateway, GatewayTypeType


class StripeService:
    def __init__(self, business_id: Optional[int] = None) -> None:
        self.business_id = business_id
        self.api_key, self.webhook_secret = self._resolve_keys(business_id)
        if not self.api_key:
            raise ValueError("Stripe API key is not configured")
        stripe.api_key = self.api_key

    def _resolve_keys(self, business_id: Optional[int]) -> tuple[str, str]:
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
            if gateway and gateway.secret_key:
                return gateway.secret_key, gateway.webhook_secret or ""
        return settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET

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
