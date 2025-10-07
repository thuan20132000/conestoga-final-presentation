from django.contrib import admin
from .models import Staff, StaffService
from django.contrib.auth.admin import UserAdmin


class StaffServiceInline(admin.TabularInline):
    model = StaffService
    extra = 0
    fields = ['is_primary']


@admin.register(Staff)
class StaffAdmin(UserAdmin):
    """Admin interface for Staff model"""

    list_display = [
        "username",
        "get_full_name",
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
        "role",
        "business",
    ]
    search_fields = ["username", "first_name", "last_name", "email", "business", "role"]
    ordering = ["role", "username"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone", "bio")}),
        ("Business Info", {"fields": ("role", "business", "hire_date", "bio", "photo")}),
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
    inlines = [StaffServiceInline]
    
@admin.register(StaffService)
class StaffServiceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'service', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at', 'staff__business']
    search_fields = ['staff__username', 'staff__business']
    ordering = ['staff__business__name', 'staff__username', 'service', 'id']
    