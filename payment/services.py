from payment.models import Payment, PaymentStatusType
from django.db import transaction
from django.db.transaction import atomic
from django.db import transaction
from typing import TypedDict, Optional, Any
from payment.models import PaymentMethod, PaymentDiscount
from appointment.models import Appointment, AppointmentStatusType, AppointmentService
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
    metadata: dict[str, Any]



class PaymentStatsResponse(TypedDict):
    results: list[Payment]
    metadata: dict[str, int | float]

class PaymentService:
    def create_payment(
        self, 
        payment_data: CreatePaymentData, 
        discounts: list[PaymentDiscount] = None, 
        appointment_services: list[AppointmentService] = None,
        metadata: dict[str, Any] = None
    ) -> Payment:
        try:
            with transaction.atomic():
                # create appointment services
                if appointment_services:
                    for appointment_service in appointment_services:
                        appointment_service_obj, created = AppointmentService.objects.update_or_create(
                            id=appointment_service['id'],
                            defaults={
                                'service_id': appointment_service['service'],
                                'staff_id': appointment_service['staff'],
                                'is_staff_request': appointment_service['is_staff_request'],
                                'start_at': appointment_service['start_at'],
                                'end_at': appointment_service['end_at'],
                                'custom_price': appointment_service['custom_price'] or 0,
                                'tip_amount': appointment_service['tip_amount'] or 0,
                                'appointment_id': appointment_service['appointment'],
                            }
                        )
                payment = Payment.objects.create(**payment_data)    
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
                    appointment.metadata = metadata or {}
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
                    # status=PaymentStatusType.COMPLETED
                )
                
                print("payment_stats", payment_stats)
            else:
                current_timezone = timezone.get_current_timezone()
                timezone_now = timezone.now().astimezone(current_timezone)
                payment_stats = Payment.objects.filter(
                    business=business,
                    created_at__date=timezone_now.date(),
                    # status=PaymentStatusType.COMPLETED
                )

            results = payment_stats.all()
            total_payments = payment_stats.count()
            total_amount = payment_stats.aggregate(total=Sum('amount'))['total'] or 0
            total_processing_fees = payment_stats.aggregate(total=Sum('processing_fee'))['total'] or 0
            total_net_amount = payment_stats.aggregate(total=Sum('net_amount'))['total'] or 0
            total_completed_payments = payment_stats.filter(status=PaymentStatusType.COMPLETED).count()
            total_completed_amount = payment_stats.filter(status=PaymentStatusType.COMPLETED).aggregate(total=Sum('amount'))['total'] or 0
            total_pending_payments = payment_stats.filter(status=PaymentStatusType.PENDING).count()
            total_pending_amount = payment_stats.filter(status=PaymentStatusType.PENDING).aggregate(total=Sum('amount'))['total'] or 0
            total_failed_payments = payment_stats.filter(status=PaymentStatusType.FAILED).count()
            total_failed_amount = payment_stats.filter(status=PaymentStatusType.FAILED).aggregate(total=Sum('amount'))['total'] or 0
            total_refunded_payments = payment_stats.filter(status=PaymentStatusType.REFUNDED).count()
            total_refunded_amount = payment_stats.filter(status=PaymentStatusType.REFUNDED).aggregate(total=Sum('amount'))['total'] or 0
            
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
                'total_other_payments': total_other_payments,
                'total_completed_amount': total_completed_amount,
                'total_pending_amount': total_pending_amount,
                'total_failed_amount': total_failed_amount,
                'total_refunded_amount': total_refunded_amount,
            }
            
            return PaymentStatsResponse(
                results=results,
                metadata=response_data
            )

        except Exception as e:
            raise Exception(f"Error getting payment stats: {e}")
        

class POSPaymentService:
    def create_appointment_and_payment(
        self, 
        appointment_data: dict[str, Any],
        payment_data: dict[str, Any],
        discounts: list[PaymentDiscount] = None,
        appointment_services: list[AppointmentService] = None,
        metadata: dict[str, Any] = None
    ) -> dict[str, Any]:
        try:
            with transaction.atomic():
                print("payment_data:: ", payment_data)
                print("appointment_services:: ", appointment_services)
                
                # create appointment
                appointment = Appointment.objects.create(
                    business_id=appointment_data['business'],
                    client_id=appointment_data['client'],
                    appointment_date=appointment_data['appointment_date'],
                    booking_source=appointment_data['booking_source'],
                    start_at=appointment_data['start_at'],
                    end_at=appointment_data['end_at'],
                )
                
                print("appointment:: ", appointment)
                
                
                # # create appointment services
                if appointment_services:
                    for appointment_service in appointment_services:
                        appointment_service_obj = AppointmentService.objects.create(
                            appointment=appointment,
                            service_id=appointment_service['service'] or None,
                            staff_id=appointment_service['staff'] or None,
                            is_staff_request=appointment_service['is_staff_request'],
                            start_at=appointment_service['start_at'],
                            end_at=appointment_service['end_at'],
                            custom_price=appointment_service['custom_price'] or 0,
                            tip_amount=appointment_service['tip_amount'] or 0,
                        )
                        
                        print("appointment_service_obj1111:: ", appointment_service_obj)
                        
                print("payment_data:: ", payment_data)
                print("appointment.id:: ", appointment.id)
                payment = Payment.objects.create(
                    payment_method_id=payment_data['payment_method'],
                    payment_method_type=payment_data['payment_method_type'],
                    business_id=payment_data['business'],
                    amount=payment_data['amount'],
                    currency=payment_data['currency'],
                    processing_fee=payment_data['processing_fee'],
                    status=payment_data['status'],
                    appointment_id=appointment.id,
                )
                
                print("payment result:: ", payment.__dict__)
                
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
                    appointment.payment_status = payment.status
                    appointment.status = AppointmentStatusType.CHECKED_OUT
                    appointment.metadata = metadata or {}
                    appointment.save()
                    
                if payment.status == PaymentStatusType.PENDING:
                    appointment.payment_status = payment.status
                    appointment.status = AppointmentStatusType.PENDING_PAYMENT
                    appointment.save()
                    
                return True
        except Exception as e:
            print("error creating appointment and payment", e)
            raise Exception(f"Error creating payment: {e}")