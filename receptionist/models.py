from django.db import models
from django.utils import timezone


class Business(models.Model):
    """Represents a salon or company using the AI receptionist."""
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=100, default="America/Toronto")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AIConfiguration(models.Model):
    """Stores AI behavior and integration settings."""
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="ai_config")
    ai_name = models.CharField(max_length=100, default="Receptionist AI")
    greeting_message = models.TextField(default="Hello! How can I help you today?")
    language = models.CharField(max_length=10, default="en")
    voice_provider = models.CharField(max_length=100, default="ElevenLabs")
    stt_provider = models.CharField(max_length=100, default="Whisper")
    model_name = models.CharField(max_length=100, default="gpt-5")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=500)
    webhook_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="calls")
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
