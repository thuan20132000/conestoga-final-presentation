from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Appointment, Client, AppointmentStatus, AppointmentReminder, AppointmentConflict, AppointmentService
)


@admin.register(AppointmentService)
class AppointmentServiceAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'service', 'staff', 'is_requested', 'custom_price', 'custom_duration', 'is_active']
    search_fields = ['service__name', 'staff__first_name', 'staff__last_name', 'appointment__client__first_name']
    ordering = ['appointment', 'service__name']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Appointment Service Information', {
            'fields': ('appointment', 'service', 'staff', 'is_requested', 'is_active')
        }),
        ('Pricing & Duration', {
            'fields': ('custom_price', 'custom_duration'),
            'classes': ('collapse',)
        }),
        ('Timing Details', {
            'fields': ('start_time', 'end_time', 'duration_minutes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(AppointmentStatus)
class AppointmentStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'sort_order']
    list_filter = ['is_active']
    ordering = ['sort_order', 'name']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


class AppointmentReminderInline(admin.TabularInline):
    model = AppointmentReminder
    extra = 0
    readonly_fields = ['sent_time', 'is_sent', 'is_delivered']
    fields = ['reminder_type', 'scheduled_time', 'sent_time', 'is_sent', 'is_delivered', 'delivery_status']


class AppointmentConflictInline(admin.TabularInline):
    model = AppointmentConflict
    fk_name = 'appointment'
    extra = 0
    readonly_fields = ['conflicting_appointment']
    fields = ['conflicting_appointment', 'conflict_type', 'description', 'is_resolved']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 'service_name', 'staff_name', 'appointment_date', 
        'start_time', 'status_display', 'is_paid'
    ]
    list_filter = [
        'appointment_date', 'status', 'is_paid', 'booking_source', 
        'is_recurring', 'business', 'created_at'
    ]
    search_fields = [
        'client__first_name', 'client__last_name', 'service__name',
        'staff__first_name', 'staff__last_name', 'notes'
    ]
    ordering = ['appointment_date', 'start_time']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': (
                'business', 'client', 'service', 'staff', 'appointment_date', 
                'start_time', 'end_time', 'duration_minutes', 'status'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('service_price', 'tax_amount', 'total_price'),
            'classes': ('collapse',)
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_method', 'payment_notes'),
            'classes': ('collapse',)
        }),
        ('Booking Information', {
            'fields': ('booked_by', 'booking_source'),
            'classes': ('collapse',)
        }),
        ('Recurring', {
            'fields': ('is_recurring', 'recurring_pattern', 'recurring_end_date', 'parent_appointment'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AppointmentReminderInline, AppointmentConflictInline]
    
    def client_name(self, obj):
        return obj.client.get_full_name()
    client_name.short_description = 'Client'
    client_name.admin_order_field = 'client__last_name'
    
    def service_name(self, obj):
        return obj.service.name
    service_name.short_description = 'Service'
    service_name.admin_order_field = 'service__name'
    
    def staff_name(self, obj):
        return obj.staff.get_full_name() if obj.staff else 'Not Assigned'
    staff_name.short_description = 'Staff'
    staff_name.admin_order_field = 'staff__last_name'
    
    def status_display(self, obj):
        color = obj.status.color if obj.status else '#6c757d'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.status.get_name_display() if obj.status else 'No Status'
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status__name'
    
@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = [
        'appointment', 'reminder_type', 'scheduled_time', 'sent_time', 
        'is_sent', 'is_delivered', 'delivery_status'
    ]
    list_filter = ['reminder_type', 'is_sent', 'is_delivered', 'scheduled_time']
    search_fields = ['appointment__client__first_name', 'appointment__client__last_name']
    readonly_fields = ['sent_time', 'created_at']
    ordering = ['scheduled_time']

@admin.register(AppointmentConflict)
class AppointmentConflictAdmin(admin.ModelAdmin):
    list_display = [
        'appointment', 'conflicting_appointment', 'conflict_type', 
        'is_resolved', 'created_at'
    ]
    list_filter = ['conflict_type', 'is_resolved', 'created_at']
    search_fields = [
        'appointment__client__first_name', 'appointment__client__last_name',
        'conflicting_appointment__client__first_name', 'conflicting_appointment__client__last_name'
    ]
    readonly_fields = ['resolved_at', 'created_at']
    ordering = ['created_at']
    
    fieldsets = (
        ('Conflict Details', {
            'fields': ('appointment', 'conflicting_appointment', 'conflict_type', 'description')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )