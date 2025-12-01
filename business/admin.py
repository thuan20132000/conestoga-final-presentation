from django.contrib import admin
from django.utils.html import format_html
from .models import (
    BusinessType, Business, OperatingHours, BusinessSettings, BusinessRoles
)
from staff.models import Staff


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(BusinessRoles)
class BusinessRolesAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_deleted', 'deleted_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


class OperatingHoursInline(admin.TabularInline):
    model = OperatingHours
    extra = 0
    fields = ['day_of_week', 'is_open', 'open_time', 'close_time', 'is_break_time', 'break_start_time', 'break_end_time']


class BusinessStaffInline(admin.TabularInline):
    model = Staff
    extra = 0
    fields = ['username', 'role', 'is_active', 'hire_date', 'last_login', 'business']
    search_fields = ['username', 'role', 'is_active', 'hire_date', 'last_login', 'business']
    ordering = ['username', 'role', 'is_active', 'hire_date', 'last_login', 'business']



@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_type', 'city', 'state_province']
    list_filter = ['business_type']
    search_fields = ['name', 'description', 'address', 'city', 'phone_number', 'email']
    ordering = ['name']
    inlines = [OperatingHoursInline, BusinessStaffInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'business_type', 'description', 'cost_per_minute')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state_province', 'postal_code', 'country')
        }),
        ('Soft delete', {
            'fields': ('is_deleted', 'deleted_at')
        }),
    )




@admin.register(OperatingHours)
class OperatingHoursAdmin(admin.ModelAdmin):
    list_display = ['business', 'day_of_week', 'is_open', 'open_time', 'close_time']
    list_filter = ['business', 'day_of_week', 'is_open']
    search_fields = ['business__name']
    ordering = ['business__name', 'day_of_week']
    
@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    list_display = ['business', 'currency', 'allow_online_booking', 'auto_confirm_appointments']
    list_filter = ['allow_online_booking', 'auto_confirm_appointments', 'send_reminder_emails', 'send_reminder_sms']
    search_fields = ['business__name']
    ordering = ['business__name']
    
    fieldsets = (
        ('Booking Settings', {
            'fields': (
                'advance_booking_days', 'min_advance_booking_hours', 'max_advance_booking_days',
                'time_slot_interval', 'buffer_time_minutes', 'timezone'
            )
        }),
        ('Notification Settings', {
            'fields': (
                'send_reminder_emails', 'send_reminder_sms', 'reminder_hours_before',
                'send_confirmation_sms'
            )
        }),
        ('Payment Settings', {
            'fields': (
                'currency', 'tax_rate', 'require_payment_advance'
            )
        }),
        ('General Settings', {
            'fields': (
                'allow_online_booking', 'require_client_phone', 'require_client_email',
                'auto_confirm_appointments'
            )
        }),
    )
