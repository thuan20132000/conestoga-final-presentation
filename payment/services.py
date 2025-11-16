from payment.models import Payment, PaymentStatusType
from django.db import transaction
from django.db.transaction import atomic
from django.db import transaction
from typing import TypedDict, Optional, Any
from payment.models import PaymentMethod, PaymentDiscount
from appointment.models import Appointment, AppointmentStatusType
from django.utils import timezone
from business.models import Business
from django.db.models import Sum, Count
from datetime import datetime
from client.models import Client
class CreatePaymentData(TypedDict):
    payment_method_id: int
    business_id: int
    client_id: int
    appointment_id: int
    amount: float
    currency: str
    external_transaction_id: str



class PaymentStatsResponse(TypedDict):
    results: list[Payment]
    metadata: dict[str, int | float]

class PaymentService:
    def create_payment(self, data, discounts: list[PaymentDiscount] = None) -> Payment:
        try:
            with transaction.atomic():
                payment = Payment.objects.create(**data)
                print("created payment", payment)
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

                if payment.status == PaymentStatusType.COMPLETED:
                    appointment = payment.appointment
                    appointment.payment_status = payment.status
                    appointment.status = AppointmentStatusType.CHECKED_OUT
                    appointment.save()
                    
                if payment.status == PaymentStatusType.PENDING:
                    appointment = payment.appointment
                    appointment.payment_status = payment.status
                    appointment.status = AppointmentStatusType.PENDING_PAYMENT
                    appointment.save()
                    
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


    def get_payment_stats(self, business: Business, from_date: datetime, to_date: datetime) -> PaymentStatsResponse:
        try:

            current_timezone = timezone.get_current_timezone()

            if from_date and to_date:
                current_timezone = timezone.get_current_timezone()
                timezone_from_date = datetime.strptime(from_date, '%Y-%m-%d').astimezone(current_timezone)
                timezone_to_date = datetime.strptime(to_date, '%Y-%m-%d').astimezone(current_timezone)
                
                payment_stats = Payment.objects.filter(
                    business=business,
                    created_at__range=(timezone_from_date, timezone_to_date),
                    status=PaymentStatusType.COMPLETED
                )
            else:
                current_timezone = timezone.get_current_timezone()
                timezone_now = timezone.now().astimezone(current_timezone)
                payment_stats = Payment.objects.filter(
                    business=business,
                    created_at__date=timezone_now.date(),
                    status=PaymentStatusType.COMPLETED
                )

            results = payment_stats.all()
            total_payments = payment_stats.count()
            total_amount = payment_stats.aggregate(total=Sum('amount'))['total'] or 0
            total_processing_fees = payment_stats.aggregate(total=Sum('processing_fee'))['total'] or 0
            total_net_amount = payment_stats.aggregate(total=Sum('net_amount'))['total'] or 0
            total_completed_payments = payment_stats.filter(status=PaymentStatusType.COMPLETED).count()
            total_pending_payments = payment_stats.filter(status=PaymentStatusType.PENDING).count()
            total_failed_payments = payment_stats.filter(status=PaymentStatusType.FAILED).count()
            total_refunded_payments = payment_stats.filter(status=PaymentStatusType.REFUNDED).count()
            
            total_cash_payments = payment_stats.filter(payment_method__name='Cash').count()
            total_credit_card_payments = payment_stats.filter(payment_method__name='Credit Card').count()
            total_debit_card_payments = payment_stats.filter(payment_method__name='Debit Card').count()
            total_bank_transfer_payments = payment_stats.filter(payment_method__name='Bank Transfer').count()
            total_cheque_payments = payment_stats.filter(payment_method__name='Cheque').count()
            total_other_payments = payment_stats.filter(payment_method__name='Other').count()
            
            
            response_data = {
                'total_payments': total_payments,
                'total_amount': total_amount,
                'total_processing_fees': total_processing_fees,
                'total_net_amount': total_net_amount,
                'total_completed_payments': total_completed_payments,
                'total_pending_payments': total_pending_payments,
                'total_failed_payments': total_failed_payments,
                'total_refunded_payments': total_refunded_payments,
                'total_cash_payments': total_cash_payments,
                'total_credit_card_payments': total_credit_card_payments,
                'total_debit_card_payments': total_debit_card_payments,
                'total_bank_transfer_payments': total_bank_transfer_payments,
                'total_cheque_payments': total_cheque_payments,
                'total_other_payments': total_other_payments
            }
            
            return PaymentStatsResponse(
                results=results,
                metadata=response_data
            )

        except Exception as e:
            raise Exception(f"Error getting payment stats: {e}")
        