from rest_framework import serializers
from django.utils import timezone
from .models import (
    PaymentMethod, Payment, PaymentDiscount, Refund
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


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'amount', 'status', 'created_at', 'updated_at', 'refund_type', 'refund_reason', 'notes']
        read_only_fields = ['created_at', 'updated_at']

class PaymentSerializer(serializers.ModelSerializer):
    
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    class Meta:
        model = Payment
        fields = [
            'id',
            'payment_method',
            'payment_method_name',
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
            'internal_notes',
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
            'status',
        ]


class PaymentDetailSerializer(PaymentSerializer):
    discounts = PaymentDiscountSerializer(many=True, read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    refund = PaymentRefundSerializer(read_only=True)
    class Meta(PaymentSerializer.Meta):
        model = Payment
        fields = PaymentSerializer.Meta.fields + ['discounts', 'payment_method_name', 'refund']
        read_only_fields = PaymentSerializer.Meta.read_only_fields + ['refund']
        
        

class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'payment', 'amount', 'status', 'created_at', 'updated_at', 'refund_type', 'refund_reason', 'notes']
        read_only_fields = ['created_at', 'updated_at']

class PaymentRefundCreateSerializer(PaymentRefundSerializer):
    class Meta(PaymentRefundSerializer.Meta):
        fields = ['payment', 'amount', 'refund_type', 'refund_reason', 'notes']