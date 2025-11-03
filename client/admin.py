from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Client




@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'is_active', 'is_vip', 'created_at', 'updated_at']
    list_filter = ['is_active', 'is_vip', 'created_at', 'updated_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering = ['last_name', 'first_name']
    list_per_page = 25
    list_max_show_all = 100
    list_editable = ['is_active', 'is_vip']
    list_display_links = ['first_name', 'last_name']
    list_filter = ['is_active', 'is_vip', 'created_at', 'updated_at']
