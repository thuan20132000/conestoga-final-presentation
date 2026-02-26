from __future__ import annotations

from datetime import datetime, timezone as dt_timezone

from .models import BusinessSubscription, SubscriptionPlan, SubscriptionStatus, BillingCycle
from payment.stripe_service import StripeService

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

BILLING_CYCLE_INTERVAL = {
    BillingCycle.MONTHLY: ('month', 1),
    BillingCycle.QUARTERLY: ('month', 3),
    BillingCycle.YEARLY: ('year', 1),
}

PRICE_ID_FIELD = {
    BillingCycle.MONTHLY: 'stripe_price_id_monthly',
    BillingCycle.QUARTERLY: 'stripe_price_id_quarterly',
    BillingCycle.YEARLY: 'stripe_price_id_yearly',
}


def _ts_to_datetime(ts) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=dt_timezone.utc)


class SubscriptionService:
    def __init__(self):
        self.stripe = StripeService()

    def get_or_create_stripe_customer(self, business) -> str:
        try:
            sub = business.subscription
            if sub.stripe_customer_id:
                return sub.stripe_customer_id
        except BusinessSubscription.DoesNotExist:
            pass

        customer = self.stripe.create_customer(
            email=business.email or '',
            name=business.name,
            metadata={'business_id': str(business.id)},
        )
        return customer.id

    def create_subscription(self, business, plan_id: int, billing_cycle: str) -> tuple:
        """
        Returns (BusinessSubscription, client_secret | None).
        client_secret is present when payment confirmation is required (no trial).
        Frontend must call stripe.confirmCardPayment(client_secret) to activate.
        """
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        price_id = getattr(plan, PRICE_ID_FIELD[billing_cycle])
        if not price_id:
            raise ValueError(
                f"Plan '{plan.name}' has no Stripe price ID for billing cycle '{billing_cycle}'. "
                "Run sync_subscription_plans first."
            )

        customer_id = self.get_or_create_stripe_customer(business)
        stripe_sub = self.stripe.create_subscription(
            customer_id=customer_id,
            price_id=price_id,
            trial_days=plan.trial_days,
        )
        print("=================  Subscription stripe_sub:: ", stripe_sub)
        
        latest_invoice = self.stripe.retrieve_invoice(stripe_sub.latest_invoice.id)
        
        print("================= Create Subscription latest_invoice:: ", latest_invoice.confirmation_secret)
        client_secret = latest_invoice.confirmation_secret
       
        sub, _ = BusinessSubscription.objects.update_or_create(
            business=business,
            defaults={
                'plan': plan,
                'billing_cycle': billing_cycle,
                'status': stripe_sub.get('status', SubscriptionStatus.TRIALING),
                'stripe_subscription_id': stripe_sub.id,
                'stripe_customer_id': customer_id,
                'current_period_start': _ts_to_datetime(stripe_sub.get('current_period_start')),
                'current_period_end': _ts_to_datetime(stripe_sub.get('current_period_end')),
                'cancel_at_period_end': stripe_sub.get('cancel_at_period_end', False),
                'trial_end': _ts_to_datetime(stripe_sub.get('trial_end')),
                'cancelled_at': None,
                'is_active': True,
                'is_deleted': False,
                'deleted_at': None,
            },
        )
        return sub, client_secret

    def cancel_subscription(
        self,
        business_subscription: BusinessSubscription,
        immediate: bool = False,
    ) -> BusinessSubscription:
       
        try:
            if business_subscription.stripe_subscription_id:
                stripe_sub = self.stripe.cancel_subscription(
                    subscription_id=business_subscription.stripe_subscription_id,
                    at_period_end=not immediate,
                )

            if immediate:
                business_subscription.status = SubscriptionStatus.CANCELLED
                business_subscription.cancelled_at = dt_timezone.now()
                business_subscription.is_active = False
            else:
                business_subscription.cancel_at_period_end = True
                business_subscription.status = stripe_sub.get('status', business_subscription.status)
                business_subscription.is_active = True

            business_subscription.save()
            return business_subscription
        
        except Exception as e:
            logger.error("Cancel Subscription error: %s", e)
            
            business_subscription.status = SubscriptionStatus.CANCELLED
            business_subscription.cancelled_at = dt_timezone.now()
            business_subscription.is_active = False
           
            business_subscription.save()
            return business_subscription
            
       
        
    def change_plan(self, business_subscription: BusinessSubscription, new_plan_id: int, new_billing_cycle: str) -> BusinessSubscription:
        plan = SubscriptionPlan.objects.get(id=new_plan_id, is_active=True)
        price_id = getattr(plan, PRICE_ID_FIELD[new_billing_cycle])
        if not price_id:
            raise ValueError(
                f"Plan '{plan.name}' has no Stripe price ID for billing cycle '{new_billing_cycle}'. "
                "Run sync_subscription_plans first."
            )

        stripe_sub = self.stripe.change_subscription_plan(
            subscription_id=business_subscription.stripe_subscription_id,
            new_price_id=price_id,
        )

        business_subscription.plan = plan
        business_subscription.billing_cycle = new_billing_cycle
        business_subscription.status = stripe_sub.get('status', business_subscription.status)
        business_subscription.current_period_start = _ts_to_datetime(stripe_sub.get('current_period_start'))
        business_subscription.current_period_end = _ts_to_datetime(stripe_sub.get('current_period_end'))
        business_subscription.cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
        business_subscription.save()
        return business_subscription

    def handle_webhook_event(self, event) -> None:
        event_type = event.get('type')
        data_object = event.get('data', {}).get('object', {})

        handlers = {
            'customer.subscription.created': self._handle_subscription_updated,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_deleted,
            'invoice.payment_succeeded': self._handle_invoice_payment_succeeded,
            'invoice.payment_failed': self._handle_invoice_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                handler(data_object)
            except Exception as e:
                logger.error("Error handling subscription webhook event %s: %s", event_type, e)

    def _get_subscription_by_stripe_id(self, stripe_sub_id: str):
        return BusinessSubscription.objects.filter(stripe_subscription_id=stripe_sub_id).first()

    def _handle_subscription_updated(self, subscription_obj) -> None:
        stripe_sub_id = subscription_obj.get('id')
        sub = self._get_subscription_by_stripe_id(stripe_sub_id)
        if not sub:
            logger.warning("No BusinessSubscription found for stripe_subscription_id=%s", stripe_sub_id)
            return

        sub.status = subscription_obj.get('status', sub.status)
        sub.current_period_start = _ts_to_datetime(subscription_obj.get('current_period_start'))
        sub.current_period_end = _ts_to_datetime(subscription_obj.get('current_period_end'))
        sub.cancel_at_period_end = subscription_obj.get('cancel_at_period_end', False)
        sub.trial_end = _ts_to_datetime(subscription_obj.get('trial_end'))
        sub.save()

    def _handle_subscription_deleted(self, subscription_obj) -> None:
        stripe_sub_id = subscription_obj.get('id')
        sub = self._get_subscription_by_stripe_id(stripe_sub_id)
        if not sub:
            return

        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = dt_timezone.now()
        sub.is_active = False
        sub.save()

    def _handle_invoice_payment_succeeded(self, invoice_obj) -> None:
        stripe_sub_id = invoice_obj.get('subscription')
        if not stripe_sub_id:
            return

        sub = self._get_subscription_by_stripe_id(stripe_sub_id)
        if not sub:
            return

        sub.status = SubscriptionStatus.ACTIVE
        sub.is_active = True
        # Refresh period dates from latest invoice if available
        period_end = invoice_obj.get('lines', {}).get('data', [{}])[0].get('period', {}).get('end')
        period_start = invoice_obj.get('lines', {}).get('data', [{}])[0].get('period', {}).get('start')
        if period_start:
            sub.current_period_start = _ts_to_datetime(period_start)
        if period_end:
            sub.current_period_end = _ts_to_datetime(period_end)
        sub.save()

    def _handle_invoice_payment_failed(self, invoice_obj) -> None:
        stripe_sub_id = invoice_obj.get('subscription')
        if not stripe_sub_id:
            return

        sub = self._get_subscription_by_stripe_id(stripe_sub_id)
        if not sub:
            return

        sub.status = SubscriptionStatus.PAST_DUE
        sub.save()
