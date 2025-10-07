from rest_framework import serializers

from .models import Notification, PushDevice


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "channel",
            "to",
            "title",
            "body",
            "data",
            "status",
            "error_message",
            "created_at",
            "sent_at",
        ]
        read_only_fields = ("status", "error_message", "created_at", "sent_at")


class PushDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushDevice
        fields = ["id", "user", "provider", "token", "active", "created_at"]
        read_only_fields = ("created_at",)
