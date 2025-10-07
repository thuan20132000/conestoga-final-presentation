from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class PaymentMethod(models.Model):
    """Payment method configurations for businesses"""
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('gift_card', 'Gift Card'),
        ('store_credit', 'Store Credit'),
        ('split_payment', 'Split Payment'),
        ('other', 'Other'),
    ]
    
    business = models.ForeignKey(
        'business.Business', on_delete=models.CASCADE, related_name='payment_methods')
    name = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    processing_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=4, default=0, 
        help_text="Processing fee as decimal (0.025 = 2.5%)")
    processing_fee_fixed = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Fixed processing fee amount")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per business
        if self.is_default:
            PaymentMethod.objects.filter(
                business=self.business, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentStatus(models.Model):
    """Payment status definitions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        ('chargeback', 'Chargeback'),
    ]
    
    name = models.CharField(max_length=50, choices=STATUS_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Hex color for UI display")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Payment Statuses'
    
    def __str__(self):
        return self.get_name_display()


class Payment(models.Model):
    """Main payment model for tracking payments"""
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('partial_refund', 'Partial Refund'),
        ('chargeback', 'Chargeback'),
        ('adjustment', 'Adjustment'),
    ]
    
    # Unique identifier
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Related entities
    business = models.ForeignKey(
        'business.Business', on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(
        'client.Client', on_delete=models.CASCADE, related_name='payments')
    appointment = models.ForeignKey(
        'appointment.Appointment', on_delete=models.CASCADE, 
        related_name='payments', null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default="CAD")
    
    # Payment method and status
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.PROTECT, related_name='payments')
    status = models.ForeignKey(
        PaymentStatus, on_delete=models.PROTECT, related_name='payments')
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPE_CHOICES, default='payment')
    external_transaction_id = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="External payment processor transaction ID")
    
    # Processing fees
    processing_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Processing fee amount charged")
    net_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Amount after processing fees")
    
    # Payment processing
    gateway_response = models.JSONField(
        blank=True, null=True,
        help_text="Raw response from payment gateway")
    failure_reason = models.TextField(blank=True, null=True)
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(
        blank=True, null=True,
        help_text="Internal notes (not visible to client)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Staff tracking
    processed_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='processed_payments')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['business', 'created_at']),
            models.Index(fields=['client', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.client.get_full_name()} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Calculate processing fee
        if self.payment_method:
            percentage_fee = self.amount * self.payment_method.processing_fee_percentage
            self.processing_fee = percentage_fee + self.payment_method.processing_fee_fixed
            self.net_amount = self.amount - self.processing_fee
        else:
            self.processing_fee = 0
            self.net_amount = self.amount
        
        # Set processed_at timestamp when status changes to completed
        if self.status and self.status.name == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        return self.status and self.status.name == 'completed'
    
    @property
    def is_pending(self):
        return self.status and self.status.name == 'pending'
    
    @property
    def is_failed(self):
        return self.status and self.status.name == 'failed'
    
    @property
    def is_refunded(self):
        return self.status and self.status.name in ['refunded', 'partially_refunded']


class PaymentSplit(models.Model):
    """For split payments across multiple payment methods"""
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='splits')
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.PROTECT, related_name='payment_splits')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))])
    processing_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    status = models.ForeignKey(
        PaymentStatus, on_delete=models.PROTECT, related_name='payment_splits')
    external_transaction_id = models.CharField(
        max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Split {self.payment.payment_id} - {self.payment_method.name} - ${self.amount}"


class Refund(models.Model):
    """Track refunds for payments"""
    REFUND_TYPE_CHOICES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
        ('chargeback', 'Chargeback'),
    ]
    
    REFUND_REASON_CHOICES = [
        ('client_request', 'Client Request'),
        ('service_issue', 'Service Issue'),
        ('cancellation', 'Cancellation'),
        ('duplicate_payment', 'Duplicate Payment'),
        ('fraud', 'Fraud'),
        ('chargeback', 'Chargeback'),
        ('other', 'Other'),
    ]
    
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='refunds')
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPE_CHOICES)
    refund_reason = models.CharField(max_length=30, choices=REFUND_REASON_CHOICES)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))])
    external_refund_id = models.CharField(
        max_length=255, blank=True, null=True)
    status = models.ForeignKey(
        PaymentStatus, on_delete=models.PROTECT, related_name='refunds')
    notes = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='processed_refunds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund {self.id} - {self.payment.payment_id} - ${self.amount}"


class PaymentTransaction(models.Model):
    """Detailed transaction log for audit trail"""
    TRANSACTION_EVENT_CHOICES = [
        ('payment_initiated', 'Payment Initiated'),
        ('payment_processed', 'Payment Processed'),
        ('payment_completed', 'Payment Completed'),
        ('payment_failed', 'Payment Failed'),
        ('refund_initiated', 'Refund Initiated'),
        ('refund_completed', 'Refund Completed'),
        ('chargeback_received', 'Chargeback Received'),
        ('status_changed', 'Status Changed'),
    ]
    
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name='transactions')
    event_type = models.CharField(max_length=30, choices=TRANSACTION_EVENT_CHOICES)
    previous_status = models.ForeignKey(
        PaymentStatus, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='previous_transactions')
    new_status = models.ForeignKey(
        PaymentStatus, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='new_transactions')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction {self.id} - {self.payment.payment_id} - {self.event_type}"


class PaymentGateway(models.Model):
    """Payment gateway configurations"""
    GATEWAY_TYPE_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('square', 'Square'),
        ('moneris', 'Moneris'),
        ('interac', 'Interac'),
        ('custom', 'Custom'),
    ]
    
    business = models.ForeignKey(
        'business.Business', on_delete=models.CASCADE, related_name='payment_gateways')
    name = models.CharField(max_length=100)
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Configuration (encrypted in production)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    secret_key = models.CharField(max_length=255, blank=True, null=True)
    webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    merchant_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Settings
    supports_refunds = models.BooleanField(default=True)
    supports_partial_refunds = models.BooleanField(default=True)
    supports_recurring = models.BooleanField(default=False)
    test_mode = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default gateway per business
        if self.is_default:
            PaymentGateway.objects.filter(
                business=self.business, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)