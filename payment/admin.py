from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    PaymentMethod, PaymentStatus, Payment, PaymentSplit, 
    Refund, PaymentTransaction, PaymentGateway
)


@admin.register(PaymentStatus)
class PaymentStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'sort_order']
    list_filter = ['is_active']
    ordering = ['sort_order', 'name']
    search_fields = ['name', 'description']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'payment_type', 'is_active', 'is_default', 'processing_fee_display']
    list_filter = ['payment_type', 'is_active', 'is_default', 'business']
    search_fields = ['name', 'description', 'business__name']
    ordering = ['business__name', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('business', 'name', 'payment_type', 'description')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default')
        }),
        ('Processing Fees', {
            'fields': ('processing_fee_percentage', 'processing_fee_fixed'),
            'description': 'Processing fees charged for this payment method'
        }),
    )
    
    def processing_fee_display(self, obj):
        if obj.processing_fee_percentage > 0 or obj.processing_fee_fixed > 0:
            return f"{obj.processing_fee_percentage:.2%} + ${obj.processing_fee_fixed}"
        return "No fees"
    processing_fee_display.short_description = 'Processing Fees'


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'gateway_type', 'is_active', 'is_default', 'test_mode']
    list_filter = ['gateway_type', 'is_active', 'is_default', 'test_mode', 'business']
    search_fields = ['name', 'business__name']
    ordering = ['business__name', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('business', 'name', 'gateway_type')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_default', 'test_mode')
        }),
        ('Capabilities', {
            'fields': ('supports_refunds', 'supports_partial_refunds', 'supports_recurring')
        }),
        ('Configuration', {
            'fields': ('api_key', 'secret_key', 'webhook_secret', 'merchant_id'),
            'classes': ('collapse',)
        }),
    )


class PaymentSplitInline(admin.TabularInline):
    model = PaymentSplit
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['payment_method', 'amount', 'processing_fee', 'status', 'external_transaction_id']


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['refund_type', 'refund_reason', 'amount', 'status', 'external_refund_id', 'notes']


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ['created_at']
    fields = ['event_type', 'description', 'amount', 'created_by']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_id', 'client_name', 'business', 'amount', 'currency',
        'payment_method_display', 'status_display', 'transaction_type',
        'created_at', 'completed_at'
    ]
    list_filter = [
        'status', 'transaction_type', 'currency', 'business', 'payment_method__payment_type',
        'created_at', 'completed_at'
    ]
    search_fields = [
        'payment_id', 'client__first_name', 'client__last_name',
        'external_transaction_id', 'appointment__service__name'
    ]
    readonly_fields = [
        'payment_id', 'created_at', 'updated_at', 'processed_at', 'completed_at',
        'processing_fee', 'net_amount'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'payment_id', 'business', 'client', 'appointment',
                'amount', 'currency', 'transaction_type'
            )
        }),
        ('Payment Method & Status', {
            'fields': (
                'payment_method', 'status', 'external_transaction_id',
                'gateway_response', 'failure_reason'
            )
        }),
        ('Financial Details', {
            'fields': ('processing_fee', 'net_amount'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Staff Tracking', {
            'fields': ('processed_by',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PaymentSplitInline, RefundInline, PaymentTransactionInline]
    
    def client_name(self, obj):
        return obj.client.get_full_name()
    client_name.short_description = 'Client'
    client_name.admin_order_field = 'client__first_name'
    
    def payment_method_display(self, obj):
        return f"{obj.payment_method.name} ({obj.payment_method.get_payment_type_display()})"
    payment_method_display.short_description = 'Payment Method'
    payment_method_display.admin_order_field = 'payment_method__name'
    
    def status_display(self, obj):
        color = obj.status.color if obj.status else "#6c757d"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.status.name if obj.status else 'Unknown'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'business', 'client', 'appointment', 'payment_method', 'status', 'processed_by'
        )


@admin.register(PaymentSplit)
class PaymentSplitAdmin(admin.ModelAdmin):
    list_display = [
        'payment_link', 'payment_method', 'amount', 'processing_fee',
        'status_display', 'created_at'
    ]
    list_filter = ['status', 'payment_method__payment_type', 'created_at']
    search_fields = ['payment__payment_id', 'payment_method__name', 'external_transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def payment_link(self, obj):
        url = reverse('admin:payment_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">{}</a>', url, obj.payment.payment_id)
    payment_link.short_description = 'Payment'
    payment_link.admin_order_field = 'payment__payment_id'
    
    def status_display(self, obj):
        color = obj.status.color if obj.status else "#6c757d"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.status.name if obj.status else 'Unknown'
        )
    status_display.short_description = 'Status'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        'payment_link', 'refund_type', 'refund_reason', 'amount',
        'status_display', 'processed_by', 'created_at'
    ]
    list_filter = [
        'refund_type', 'refund_reason', 'status', 'created_at'
    ]
    search_fields = [
        'payment__payment_id', 'external_refund_id', 'notes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Refund Information', {
            'fields': (
                'payment', 'refund_type', 'refund_reason', 'amount',
                'external_refund_id', 'status'
            )
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_link(self, obj):
        url = reverse('admin:payment_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">{}</a>', url, obj.payment.payment_id)
    payment_link.short_description = 'Payment'
    payment_link.admin_order_field = 'payment__payment_id'
    
    def status_display(self, obj):
        color = obj.status.color if obj.status else "#6c757d"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.status.name if obj.status else 'Unknown'
        )
    status_display.short_description = 'Status'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'payment_link', 'event_type', 'amount', 'created_at', 'created_by'
    ]
    list_filter = ['event_type', 'created_at']
    search_fields = ['payment__payment_id', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def payment_link(self, obj):
        url = reverse('admin:payment_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">{}</a>', url, obj.payment.payment_id)
    payment_link.short_description = 'Payment'
    payment_link.admin_order_field = 'payment__payment_id'


# Customize admin site headers
admin.site.site_header = "BookNgon AI - Payment Management"
admin.site.site_title = "Payment Admin"
admin.site.index_title = "Payment Management Administration"