from django.contrib import admin
from .models import StaffTurn, Turn


@admin.register(StaffTurn)
class StaffTurnAdmin(admin.ModelAdmin):
    list_filter = ['business', 'date', 'is_available']
    ordering = ['date', 'position']


@admin.register(Turn)
class TurnAdmin(admin.ModelAdmin):
    list_filter = ['status', 'staff_turn__date', 'is_client_request']
    ordering = ['-created_at']
