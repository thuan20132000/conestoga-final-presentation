from rest_framework import serializers
from django.utils import timezone
from .models import (
    PaymentMethod, Payment, PaymentDiscount
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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'payment_method',
            'business',
            'client',
            'appointment',
            'status',
            'amount',
            'currency',
            'external_transaction_id',
            'processing_fee',
            'net_amount',
            'created_at',
            'updated_at',
            'processed_at',
            'completed_at',
            'processed_by',
            'notes',
            'internal_notes'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDiscount
        fields = ['id', 'discount_amount', 'discount_percentage', 'discount_code', 'discount_description', 'created_at']
        read_only_fields = ['created_at']
    
class PaymentDiscountCreateSerializer(PaymentDiscountSerializer):
    class Meta(PaymentDiscountSerializer.Meta):
        fields = [
            'discount_amount',
            'discount_percentage',
            'discount_code', 
            'discount_description',
        ]

class PaymentCreateSerializer(PaymentSerializer):
    class Meta:
        model = Payment
        fields = [
            'payment_method',
            'business',
            'client',
            'appointment',
            'payment_method',
            'amount',
            'currency',
            'external_transaction_id',
            'processing_fee',
            'net_amount',
            'notes',
            'internal_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


