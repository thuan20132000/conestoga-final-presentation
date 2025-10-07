from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Client, ClientHistory, ClientPreference


class ClientPreferenceInline(admin.TabularInline):
    """Inline admin for client preferences"""
    model = ClientPreference
    extra = 0
    fields = ['preference_type', 'preference_key', 'preference_value']
    readonly_fields = ['created_at', 'updated_at']


class ClientHistoryInline(admin.TabularInline):
    """Inline admin for client history"""
    model = ClientHistory
    extra = 0
    readonly_fields = ['action', 'description', 'changed_by', 'changed_at']
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin interface for Client model"""
    list_display = [
        'get_full_name', 'email', 'phone', 'primary_business',
        'is_active', 'is_vip', 'age_display', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_vip', 'primary_business', 'preferred_contact_method',
        'created_at', 'city', 'state_province'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 'city',
        'state_province', 'postal_code'
    ]
    ordering = ['last_name', 'first_name']
    list_per_page = 25
    list_select_related = ['primary_business']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone', 'date_of_birth'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city',
                'state_province', 'postal_code', 'country'
            ),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences & Status', {
            'fields': (
                'preferred_contact_method', 'primary_business',
                'is_active', 'is_vip'
            )
        }),
        ('Notes', {
            'fields': ('notes', 'medical_notes'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ClientPreferenceInline, ClientHistoryInline]
    
    actions = ['make_vip', 'remove_vip', 'activate_clients', 'deactivate_clients']
    
    def get_full_name(self, obj):
        """Display full name"""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'
    
    def age_display(self, obj):
        """Display age"""
        age = obj.get_age()
        if age is not None:
            return f"{age} years"
        return "Unknown"
    age_display.short_description = 'Age'
    
    def make_vip(self, request, queryset):
        """Make selected clients VIP"""
        updated = queryset.update(is_vip=True)
        self.message_user(
            request,
            f'{updated} clients were marked as VIP.'
        )
    make_vip.short_description = "Mark selected clients as VIP"
    
    def remove_vip(self, request, queryset):
        """Remove VIP status from selected clients"""
        updated = queryset.update(is_vip=False)
        self.message_user(
            request,
            f'VIP status removed from {updated} clients.'
        )
    remove_vip.short_description = "Remove VIP status from selected clients"
    
    def activate_clients(self, request, queryset):
        """Activate selected clients"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} clients were activated.'
        )
    activate_clients.short_description = "Activate selected clients"
    
    def deactivate_clients(self, request, queryset):
        """Deactivate selected clients"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} clients were deactivated.'
        )
    deactivate_clients.short_description = "Deactivate selected clients"


@admin.register(ClientPreference)
class ClientPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for ClientPreference model"""
    list_display = ['client', 'preference_type', 'preference_key', 'preference_value', 'created_at']
    list_filter = ['preference_type', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'preference_key', 'preference_value']
    ordering = ['client__last_name', 'client__first_name', 'preference_type']
    list_select_related = ['client']
    
    fieldsets = (
        ('Preference Details', {
            'fields': ('client', 'preference_type', 'preference_key', 'preference_value')
        }),
    )


@admin.register(ClientHistory)
class ClientHistoryAdmin(admin.ModelAdmin):
    """Admin interface for ClientHistory model"""
    list_display = ['client', 'action', 'description', 'changed_by', 'changed_at']
    list_filter = ['action', 'changed_at']
    search_fields = ['client__first_name', 'client__last_name', 'description']
    ordering = ['-changed_at']
    list_select_related = ['client', 'changed_by']
    readonly_fields = ['client', 'action', 'description', 'changed_by', 'changed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False