from django.db import models
from django.utils import timezone
from .enums import AIConfigurationStatus



class AIConfiguration(models.Model):
    STATUS_CHOICES = [
        (AIConfigurationStatus.ACTIVE.value, "Active"),
        (AIConfigurationStatus.INACTIVE.value, "Inactive"),
        (AIConfigurationStatus.PENDING.value, "Pending"),
        (AIConfigurationStatus.ERROR.value, "Error"),
        (AIConfigurationStatus.DELETED.value, "Deleted"),
        (AIConfigurationStatus.ARCHIVED.value, "Archived"),
    ]
    
    LANGUAGE_CHOICES = [
        ("en-US", "English (US)"),
        ("en-GB", "English (GB)"),
        ("es-ES", "Spanish (ES)"),
        ("fr-FR", "French (FR)"),
        ("de-DE", "German (DE)"),
        ("it-IT", "Italian (IT)"),
    ]
    """Stores AI behavior and integration settings."""
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, related_name="ai_configs")
    ai_name = models.CharField(max_length=100, default="Receptionist AI")
    greeting_message = models.TextField(default="Hello! How can I help you today?")
    prompt = models.TextField(default="You are a professional AI receptionist for a Salon. Your role is to assist clients with appointments, provide business information, and answer questions about our services. Always be helpful, professional, and friendly. Use the available tools to provide accurate information from our knowledge base. If you need to book appointments, get customer information or access specific business data, use the appropriate tools.")
    language = models.CharField(max_length=10, default="en-US", choices=LANGUAGE_CHOICES)
    voice_provider = models.CharField(max_length=100, default="ElevenLabs")
    stt_provider = models.CharField(max_length=100, default="Whisper")
    model_name = models.CharField(max_length=100, default="gpt-5")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=500)
    webhook_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=AIConfigurationStatus.ACTIVE.value)
    class Meta:
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"

    def __str__(self):
        return f"{self.business.name} AI Config"


class CallSession(models.Model):
    """Tracks each phone call handled by the receptionist."""
    CALL_DIRECTION_CHOICES = [
        ("inbound", "Inbound"),
        ("outbound", "Outbound"),
    ]
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, related_name="calls")
    direction = models.CharField(max_length=20, choices=CALL_DIRECTION_CHOICES, default="inbound")
    caller_number = models.CharField(max_length=50)
    receiver_number = models.CharField(max_length=50, blank=True, null=True)
    call_sid = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    transcript_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Call {self.call_sid} - {self.caller_number}"


class ConversationMessage(models.Model):
    """Stores each message exchanged during the call."""
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class Intent(models.Model):
    """Represents detected intent from user speech (e.g., booking, cancel, inquiry)."""
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="intents")
    name = models.CharField(max_length=100)
    confidence = models.FloatField(default=0.0)
    extracted_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.confidence:.2f})"


class AudioRecording(models.Model):
    """Stores reference to call audio files."""
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="recordings")
    audio_url = models.URLField()
    duration_seconds = models.IntegerField(blank=True, null=True)
    transcription_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recording for {self.call.call_sid}"


class SystemLog(models.Model):
    """Tracks system and AI events for debugging or analytics."""
    call = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name="logs", null=True, blank=True)
    level = models.CharField(max_length=20, choices=[("info", "Info"), ("warning", "Warning"), ("error", "Error")])
    message = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[" + self.level + "] " + self.message[:50]
