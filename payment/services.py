from payment.models import Payment, PaymentStatusType
from django.db import transaction
from django.db.transaction import atomic
from django.db import transaction
from typing import TypedDict, Optional
from payment.models import PaymentMethod, PaymentDiscount


class CreatePaymentData(TypedDict):
    payment_method_id: int
    business_id: int
    client_id: int
    appointment_id: int
    amount: float
    currency: str
    external_transaction_id: str


class PaymentService:
    def create_payment(self, data, discounts: list[PaymentDiscount] = None) -> Payment:
        try:
            with transaction.atomic():
                payment = Payment.objects.create(**data)
                
                # create payment discounts
                if discounts:
                    for discount in discounts:
                        PaymentDiscount.objects.create(
                            payment=payment, 
                            discount_amount=discount.get('discount_amount', 0),
                            discount_percentage=discount.get('discount_percentage', 0),
                            discount_code=discount.get('discount_code', ''),
                            discount_description=discount.get('discount_description', '')
                            )
                
                return payment
        except Exception as e:
            raise Exception(f"Error creating payment: {e}")

    def process_payment(self, payment: Payment) -> Payment:
        payment.status = PaymentStatusType.COMPLETED
        payment.save()
        return payment

    def refund_payment(self, payment: Payment) -> Payment:
        payment.status = PaymentStatusType.REFUNDED
        payment.save()
        return payment

    def cancel_payment(self, payment: Payment) -> Payment:
        payment.status = PaymentStatusType.CANCELLED
        payment.save()
        return payment

    def update_payment(self, payment: Payment) -> Payment:
        payment.save()
        return payment

    def get_payment(self, payment_id: int) -> Payment:
        return Payment.objects.get(id=payment_id)
