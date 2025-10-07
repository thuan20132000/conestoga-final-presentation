from rest_framework import serializers
from django.utils import timezone
from django.db import models
from .models import (
    PaymentMethod, PaymentStatus, Payment, PaymentSplit, 
    Refund, PaymentTransaction, PaymentGateway
)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'payment_type', 'is_active', 'is_default',
            'processing_fee_percentage', 'processing_fee_fixed',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentStatus
        fields = [
            'id', 'name', 'description', 'color', 'is_active', 'sort_order'
        ]


class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'name', 'gateway_type', 'is_active', 'is_default',
            'supports_refunds', 'supports_partial_refunds', 
            'supports_recurring', 'test_mode', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentTransactionSerializer(serializers.ModelSerializer):
    previous_status_name = serializers.CharField(source='previous_status.name', read_only=True)
    new_status_name = serializers.CharField(source='new_status.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'event_type', 'previous_status_name', 'new_status_name',
            'amount', 'description', 'metadata', 'created_at', 'created_by_name'
        ]
        read_only_fields = ['created_at']


class PaymentSplitSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    
    class Meta:
        model = PaymentSplit
        fields = [
            'id', 'payment_method', 'payment_method_name', 'amount',
            'processing_fee', 'status_name', 'external_transaction_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(source='payment.payment_id', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment_id', 'refund_type', 'refund_reason', 'amount',
            'external_refund_id', 'status_name', 'notes', 'processed_by_name',
            'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'processed_at']


class PaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for payment list views"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    status_color = serializers.CharField(source='status.color', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    service_name = serializers.CharField(source='appointment.service.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'client_name', 'amount', 'currency',
            'payment_method_name', 'status_name', 'status_color',
            'transaction_type', 'processing_fee', 'net_amount',
            'appointment_date', 'service_name', 'created_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'completed_at']


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for payment detail views"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    payment_method_type = serializers.CharField(source='payment_method.payment_type', read_only=True)
    
    status_name = serializers.CharField(source='status.name', read_only=True)
    status_color = serializers.CharField(source='status.color', read_only=True)
    
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    # Related appointment details
    appointment_id = serializers.IntegerField(source='appointment.id', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_start_time = serializers.TimeField(source='appointment.start_time', read_only=True)
    service_name = serializers.CharField(source='appointment.service.name', read_only=True)
    staff_name = serializers.CharField(source='appointment.staff.get_full_name', read_only=True)
    
    # Related data
    splits = PaymentSplitSerializer(many=True, read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'business', 'client', 'client_name', 'client_email', 'client_phone',
            'appointment', 'appointment_id', 'appointment_date', 'appointment_start_time',
            'service_name', 'staff_name',
            'amount', 'currency', 'payment_method', 'payment_method_name', 'payment_method_type',
            'status', 'status_name', 'status_color', 'transaction_type',
            'external_transaction_id', 'processing_fee', 'net_amount',
            'gateway_response', 'failure_reason', 'notes', 'internal_notes',
            'processed_by', 'processed_by_name',
            'created_at', 'updated_at', 'processed_at', 'completed_at',
            'splits', 'refunds', 'transactions'
        ]
        read_only_fields = [
            'payment_id', 'created_at', 'updated_at', 'processed_at', 'completed_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new payments"""
    class Meta:
        model = Payment
        fields = [
            'business', 'client', 'appointment', 'amount', 'currency',
            'payment_method', 'status', 'transaction_type', 'notes'
        ]
    
    def validate(self, data):
        # Validate that the payment method belongs to the business
        if data['payment_method'].business != data['business']:
            raise serializers.ValidationError(
                "Payment method must belong to the specified business"
            )
        
        # Validate appointment belongs to client and business
        if data.get('appointment'):
            appointment = data['appointment']
            if appointment.client != data['client']:
                raise serializers.ValidationError(
                    "Appointment must belong to the specified client"
                )
            if appointment.business != data['business']:
                raise serializers.ValidationError(
                    "Appointment must belong to the specified business"
                )
        
        return data


class PaymentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payments"""
    class Meta:
        model = Payment
        fields = [
            'status', 'external_transaction_id', 'gateway_response',
            'failure_reason', 'notes', 'internal_notes', 'processed_by'
        ]
    
    def validate_status(self, value):
        # Add business logic for status transitions if needed
        return value


class PaymentSplitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment splits"""
    class Meta:
        model = PaymentSplit
        fields = [
            'payment', 'payment_method', 'amount', 'status'
        ]
    
    def validate(self, data):
        payment = data['payment']
        payment_method = data['payment_method']
        amount = data['amount']
        
        # Validate payment method belongs to same business as payment
        if payment_method.business != payment.business:
            raise serializers.ValidationError(
                "Payment method must belong to the same business as the payment"
            )
        
        # Validate split amount doesn't exceed payment amount
        existing_splits_total = PaymentSplit.objects.filter(
            payment=payment
        ).exclude(id=self.instance.id if self.instance else None).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        if existing_splits_total + amount > payment.amount:
            raise serializers.ValidationError(
                "Split amounts cannot exceed the total payment amount"
            )
        
        return data


class RefundCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating refunds"""
    class Meta:
        model = Refund
        fields = [
            'payment', 'refund_type', 'refund_reason', 'amount',
            'notes', 'processed_by'
        ]
    
    def validate_amount(self, value):
        # Validate refund amount doesn't exceed payment amount
        payment = self.initial_data.get('payment')
        if payment:
            existing_refunds_total = Refund.objects.filter(
                payment=payment
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            if existing_refunds_total + value > payment.amount:
                raise serializers.ValidationError(
                    "Refund amount cannot exceed the remaining refundable amount"
                )
        
        return value
