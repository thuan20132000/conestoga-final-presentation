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
)
from .filters import PaymentMethodFilter
from main.viewsets import BaseModelViewSet
from payment.services import PaymentService


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
            discounts = request_data.pop('discounts', None)
            serializer = PaymentCreateSerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            payment_service = PaymentService()
            
            payment = payment_service.create_payment(validated_data, discounts)
            
            return self.response_success(PaymentSerializer(payment).data)
        except Exception as e:
            print("error creating payment", e)
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


