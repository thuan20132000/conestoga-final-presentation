from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html
from .models import (
    BusinessType, 
    Business, 
    OperatingHours, 
    BusinessSettings, 
    BusinessRoles, 
    BusinessOnlineBooking,
    BusinessBanner,
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


class BusinessOwnerInlineForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text='Leave blank to set an unusable password.',
    )

    class Meta:
        model = Staff
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'phone', 'is_active']

    def save(self, commit=True):
        staff = super().save(commit=False)
        raw_password = self.cleaned_data.get('password')
        if raw_password:
            staff.set_password(raw_password)
        elif not self.instance.pk:
            staff.set_unusable_password()
        if commit:
            staff.save()
        return staff


class BusinessOwnerFormset(BaseInlineFormSet):
    role_name = 'Owner'


class BusinessOwnerInline(admin.TabularInline):
    model = Staff
    form = BusinessOwnerInlineForm
    formset = BusinessOwnerFormset
    verbose_name = 'Owner'
    verbose_name_plural = 'Owners'
    extra = 1
    fields = ['username', 'password', 'first_name', 'last_name', 'email', 'phone', 'is_active']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role__name='Owner')


class BusinessManagerInline(admin.TabularInline):
    model = Staff
    verbose_name = 'Manager'
    verbose_name_plural = 'Managers'
    extra = 0
    fields = ['first_name','phone', 'is_active', 'username']
    readonly_fields = ['first_name', 'phone', 'is_active', 'username']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role__name='Manager')


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'business_type', 'city', 'state_province']
    list_filter = ['business_type']
    search_fields = ['name', 'description', 'address', 'city', 'phone_number', 'email']
    ordering = ['name']
    inlines = [BusinessOwnerInline, BusinessManagerInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        business = form.instance
        for formset in formsets:
            if not hasattr(formset, 'role_name'):
                continue
            role, _ = BusinessRoles.objects.get_or_create(business=business, name=formset.role_name)
            for staff in formset.new_objects:
                staff.role = role
                staff.save()

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'business_type', 'description', 'cost_per_minute', 'twilio_phone_number', 'google_review_url')
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
                'send_confirmation_sms', 'send_confirmation_email',
                'send_cancellation_sms', 'send_cancellation_email',
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
                'auto_confirm_appointments', 'allow_online_gift_cards', 'gift_card_processing_fee_enabled', 'tax_with_cash_enabled'
            )
        }),
    )

@admin.register(BusinessOnlineBooking)
class BusinessOnlineBookingAdmin(admin.ModelAdmin):
    list_display = ['business', 'name', 'slug', 'is_active', 'shareable_link']
    list_filter = ['business', 'is_active']
    search_fields = ['business__name', 'name', 'slug']
    ordering = ['business__name', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'logo', 'description', 'policy')
        }),
        ('Booking Settings', {
            'fields': ('interval_minutes', 'buffer_time_minutes')
        }),
        ('Status and Visibility', {
            'fields': ('is_active', 'shareable_link')
        }),
    )

@admin.register(BusinessBanner)
class BusinessBannerAdmin(admin.ModelAdmin):
    list_display = ['business', 'type', 'title', 'message', 'cta_text', 'cta_url', 'start_at', 'end_at', 'is_active']
    list_filter = ['business', 'type', 'is_active']
    search_fields = ['business__name', 'title', 'message', 'cta_text', 'cta_url']
    ordering = ['business__name', 'type', 'title']