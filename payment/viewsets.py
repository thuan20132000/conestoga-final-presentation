from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    PaymentMethod, Payment, PaymentSplit, 
    Refund, PaymentTransaction, PaymentGateway, PaymentStatusType, PaymentDiscount
)
from .serializers import (
    PaymentMethodSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    PaymentDiscountCreateSerializer,
    PaymentRefundSerializer,
    PaymentRefundCreateSerializer,
)
from .filters import PaymentMethodFilter
from main.viewsets import BaseModelViewSet
from payment.services import PaymentService
from django.db import transaction
from payment.models import RefundTypeType
from decimal import Decimal

class PaymentMethodViewSet(BaseModelViewSet):
    """ViewSet for managing payment methods"""
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentMethodFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'is_active']
    ordering = ['name']
    
    
    def get_queryset(self):
        queryset = super().get_queryset()
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset.select_related('business')
    
    @action(detail=False, methods=['post'])
    def set_default(self, request):
        """Set a payment method as default for a business"""
        payment_method_id = request.data.get('payment_method_id')
        business_id = request.data.get('business_id')
        
        if not payment_method_id or not business_id:
            return Response(
                {'error': 'payment_method_id and business_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment_method = PaymentMethod.objects.get(
                id=payment_method_id, business_id=business_id
            )
            
            # Unset other default payment methods for this business
            PaymentMethod.objects.filter(
                business_id=business_id, is_default=True
            ).update(is_default=False)
            
            # Set this one as default
            payment_method.is_default = True
            payment_method.save()
            
            return Response({'message': 'Default payment method updated'})
            
        except PaymentMethod.DoesNotExist:
            return Response(
                {'error': 'Payment method not found'},
                status=status.HTTP_404_NOT_FOUND
            )



class PaymentViewSet(BaseModelViewSet):
    """ViewSet for managing payments"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        
        try:
            request_data = request.data.copy()
            appointment_services = request_data.get('appointment_services', None)
            discounts = request_data.get('discounts', None)
            
            serializer = PaymentCreateSerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            payment_service = PaymentService()
            
            payment = payment_service.create_payment(
                payment_data=validated_data, 
                discounts=discounts,
                appointment_services=appointment_services
            )
            
            return self.response_success(PaymentSerializer(payment).data)
        except Exception as e:
            print("error creating payment", e)
            return self.response_error(str(e))
        
    @action(detail=True, methods=['post'], url_path='refund')
    def refund(self, request, pk=None):
        """Refund a payment"""
        
        try:
            
            with transaction.atomic():
                payment = self.get_object()
                
                request_data = request.data.copy()
                refund_amount = request_data.get('amount', payment.amount)
                refund_reason = request_data.get('refund_reason', 'Refunded via API')
                refund_type = request_data.get('refund_type', RefundTypeType.FULL)
                refund_notes = request_data.get('notes', 'Refunded via API')
                
                # Use update_or_create to handle existing refunds safely (avoids UNIQUE constraint violation)
                refund, created = Refund.objects.update_or_create(
                    payment=payment,
                    defaults={
                        'amount': refund_amount,
                        'refund_type': refund_type,
                        'refund_reason': refund_reason,
                        'status': PaymentStatusType.REFUNDED,
                        'notes': refund_notes
                    }
                )
                
                payment.status = PaymentStatusType.REFUNDED
                payment_appointment = payment.appointment
                payment_appointment.payment_status = PaymentStatusType.REFUNDED
                payment_appointment.save()
                payment.save()
                
                serializer = PaymentSerializer(payment)
                
                return self.response_success(serializer.data)
            
        except Exception as e:
            print("error refunding payment", e)
            return self.response_error(str(e))
        
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process a payment (simulate payment processing)"""
        payment = self.get_object()
        
        
        if payment.is_completed:
            return Response(
                {'error': 'Payment is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulate payment processing
        payment.external_transaction_id = f"txn_{timezone.now().timestamp()}"
        payment.gateway_response = {
            'status': 'success',
            'transaction_id': payment.external_transaction_id,
            'processed_at': timezone.now().isoformat()
        }
        
        # Set status to completed
        completed_status = PaymentStatusType.COMPLETED
        payment.status = completed_status
        payment.processed_by = request.user.staff if hasattr(request.user, 'staff') else None
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def fail_payment(self, request, pk=None):
        """Mark a payment as failed"""
        payment = self.get_object()
        
        if payment.is_completed:
            return Response(
                {'error': 'Cannot fail a completed payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        failure_reason = request.data.get('failure_reason', 'Payment processing failed')
        
        payment.failure_reason = failure_reason
        failed_status = PaymentStatusType.FAILED
        payment.status = failed_status
        payment.processed_by = request.user.staff if hasattr(request.user, 'staff') else None
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)



class PaymentRefundViewSet(BaseModelViewSet):
    """ViewSet for managing payment refunds"""
    queryset = Refund.objects.all()
    serializer_class = PaymentRefundSerializer
    