from django.contrib import admin
from webpush.models import PushInformation, Group, SubscriptionInfo
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "channel", "business", "to", "status", "created_at", "sent_at")
    list_filter = ("channel", "status", "created_at", "business", "user")
    search_fields = ("to", "title", "body")
    readonly_fields = ("created_at", "sent_at")



@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_filter = ("name",)
    search_fields = ("name",)

@admin.register(SubscriptionInfo)
class SubscriptionInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "endpoint", "auth", "p256dh", "browser", "user_agent")
    list_filter = ("browser",)
    search_fields = ("endpoint",)
