from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    PaymentMethod, PaymentStatus, Payment, PaymentSplit, 
    Refund, PaymentTransaction, PaymentGateway
)
from .serializers import (
    PaymentMethodSerializer, PaymentStatusSerializer, PaymentGatewaySerializer,
    PaymentListSerializer, PaymentDetailSerializer, PaymentCreateSerializer,
    PaymentUpdateSerializer, PaymentSplitSerializer, PaymentSplitCreateSerializer,
    RefundSerializer, RefundCreateSerializer, PaymentTransactionSerializer
)
from .filters import PaymentFilter, PaymentMethodFilter, RefundFilter


class PaymentMethodViewSet(viewsets.ModelViewSet):
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


class PaymentStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for payment statuses (read-only)"""
    queryset = PaymentStatus.objects.filter(is_active=True)
    serializer_class = PaymentStatusSerializer
    ordering = ['sort_order', 'name']


class PaymentGatewayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment gateways"""
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'gateway_type']
    ordering_fields = ['name', 'created_at', 'is_active']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        business_id = self.request.query_params.get('business_id')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        return queryset.select_related('business')


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payments"""
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ['payment_id', 'client__first_name', 'client__last_name', 'external_transaction_id']
    ordering_fields = ['created_at', 'amount', 'appointment_date', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentListSerializer
        elif self.action in ['create']:
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentUpdateSerializer
        return PaymentDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'business', 'client', 'appointment', 'appointment__service',
            'appointment__staff', 'payment_method', 'status', 'processed_by'
        ).prefetch_related('splits', 'refunds', 'transactions')
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get payment dashboard statistics"""
        business_id = request.query_params.get('business_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = self.get_queryset()
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Calculate statistics
        total_payments = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_processing_fees = queryset.aggregate(total=Sum('processing_fee'))['total'] or 0
        net_amount = queryset.aggregate(total=Sum('net_amount'))['total'] or 0
        
        # Status breakdown
        status_stats = queryset.values('status__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        # Payment method breakdown
        method_stats = queryset.values('payment_method__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        # Daily stats for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        daily_stats = queryset.filter(
            created_at__date__range=[start_date, end_date]
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('day')
        
        return Response({
            'summary': {
                'total_payments': total_payments,
                'total_amount': float(total_amount),
                'total_processing_fees': float(total_processing_fees),
                'net_amount': float(net_amount),
            },
            'status_breakdown': list(status_stats),
            'payment_method_breakdown': list(method_stats),
            'daily_stats': list(daily_stats),
        })
    
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
        completed_status = PaymentStatus.objects.get(name='completed')
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
        failed_status = PaymentStatus.objects.get(name='failed')
        payment.status = failed_status
        payment.processed_by = request.user.staff if hasattr(request.user, 'staff') else None
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)


class PaymentSplitViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment splits"""
    queryset = PaymentSplit.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PaymentSplitCreateSerializer
        return PaymentSplitSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        payment_id = self.request.query_params.get('payment_id')
        if payment_id:
            queryset = queryset.filter(payment_id=payment_id)
        return queryset.select_related('payment', 'payment_method', 'status')


class RefundViewSet(viewsets.ModelViewSet):
    """ViewSet for managing refunds"""
    queryset = Refund.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RefundFilter
    search_fields = ['payment__payment_id', 'external_refund_id', 'notes']
    ordering_fields = ['created_at', 'amount', 'refund_type']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return RefundCreateSerializer
        return RefundSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'payment', 'payment__client', 'status', 'processed_by'
        )
    
    @action(detail=True, methods=['post'])
    def process_refund(self, request, pk=None):
        """Process a refund"""
        refund = self.get_object()
        
        if refund.status.name == 'completed':
            return Response(
                {'error': 'Refund is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulate refund processing
        refund.external_refund_id = f"ref_{timezone.now().timestamp()}"
        
        # Set status to completed
        completed_status = PaymentStatus.objects.get(name='completed')
        refund.status = completed_status
        refund.processed_by = request.user.staff if hasattr(request.user, 'staff') else None
        refund.processed_at = timezone.now()
        refund.save()
        
        # Update payment status if it's a full refund
        if refund.refund_type == 'full':
            payment = refund.payment
            refunded_status = PaymentStatus.objects.get(name='refunded')
            payment.status = refunded_status
            payment.save()
        
        serializer = self.get_serializer(refund)
        return Response(serializer.data)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment transactions (read-only)"""
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment', 'event_type']
    ordering_fields = ['created_at', 'event_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        payment_id = self.request.query_params.get('payment_id')
        if payment_id:
            queryset = queryset.filter(payment_id=payment_id)
        return queryset.select_related(
            'payment', 'previous_status', 'new_status', 'created_by'
        )
