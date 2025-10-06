from django.contrib import admin
from .models import (
    Business,
    AIConfiguration,
    CallSession,
    ConversationMessage,
    Intent,
    AudioRecording,
    SystemLog,
)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "timezone", "created_at")
    search_fields = ("name", "phone_number")
    list_filter = ("timezone",)


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ("business", "ai_name", "language", "voice_provider", "stt_provider", "model_name", "updated_at")
    search_fields = ("business__name", "ai_name", "model_name")
    list_filter = ("language", "voice_provider", "stt_provider")


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ("call_sid", "business", "direction", "caller_number", "receiver_number", "status", "started_at", "ended_at", "duration_seconds")
    search_fields = ("call_sid", "caller_number", "receiver_number", "business__name")
    list_filter = ("direction", "status", "business")
    date_hierarchy = "started_at"


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = ("call", "role", "short_content", "timestamp", "confidence_score")
    search_fields = ("call__call_sid", "content")
    list_filter = ("role",)

    def short_content(self, obj):
        return (obj.content[:75] + "...") if len(obj.content) > 75 else obj.content
    short_content.short_description = "Content"


@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ("call", "name", "confidence", "created_at")
    search_fields = ("call__call_sid", "name")
    list_filter = ("name",)


@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    list_display = ("call", "audio_url", "duration_seconds", "created_at")
    search_fields = ("call__call_sid", "audio_url")


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ("call", "level", "short_message", "created_at")
    search_fields = ("call__call_sid", "message")
    list_filter = ("level",)

    def short_message(self, obj):
        return (obj.message[:75] + "...") if len(obj.message) > 75 else obj.message
    short_message.short_description = "Message"
