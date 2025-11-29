from django.contrib import admin
from webpush.models import SubscriptionInfo, PushInformation, Group

from .models import Notification, PushDevice

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "channel", "business", "to", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "created_at", "business", "user")
    search_fields = ("to", "title", "body")
    readonly_fields = ("created_at", "sent_at")


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "business", "provider", "active", "created_at")
    list_filter = ("provider", "active")
    search_fields = ("token",)
    readonly_fields = ("created_at",)

@admin.register(SubscriptionInfo)
class SubscriptionInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "endpoint", "auth", "p256dh", "browser", "user_agent")
    list_filter = ("browser",)
    search_fields = ("endpoint",)

@admin.register(Group)
class WebPushGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_filter = ("name",)
    search_fields = ("name",)
