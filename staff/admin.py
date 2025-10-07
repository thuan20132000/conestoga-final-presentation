from django.contrib import admin
from .models import Staff, StaffService, StaffWorkingHours, StaffOffDay
from django.contrib.auth.admin import UserAdmin
from time import time

class StaffServiceInline(admin.TabularInline):
    model = StaffService
    extra = 0
    fields = ['service', 'is_primary']

class StaffWorkingHoursInline(admin.TabularInline):
    model = StaffWorkingHours
    extra = 0
    fields = ['day_of_week', 'start_time', 'end_time']

class StaffOffDayInline(admin.TabularInline):
    model = StaffOffDay
    extra = 0
    fields = ['start_date', 'end_date', 'reason']

@admin.register(Staff)
class StaffAdmin(UserAdmin):
    """Admin interface for Staff model"""

    list_display = [
        "username",
        "role",
        "is_active",
        "hire_date",
        "last_login",
        "business",
    ]
    list_filter = [
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "hire_date",
        "date_joined",
        "last_login",
        "business",
    ]
    search_fields = ["username", "first_name", "last_name", "email", "business", "role"]
    ordering = ["role", "username"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone", "bio")}),
        ("Business Info", {"fields": ("role", "business", "hire_date", "photo")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "role",
                    "business",
                    "hire_date",
                    "bio",
                    "photo",
                ),
            },
        ),
    )

    readonly_fields = ["date_joined", "last_login"]
    inlines = [StaffServiceInline, StaffWorkingHoursInline, StaffOffDayInline]
    
@admin.register(StaffService)
class StaffServiceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'service', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at', 'staff__business']
    search_fields = ['staff__username', 'staff__business']
    ordering = ['staff__business__name', 'staff__username', 'service', 'id']
    