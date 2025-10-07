from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Client, ClientHistory, ClientPreference

User = get_user_model()


@receiver(post_save, sender=Client)
def client_saved(sender, instance, created, **kwargs):
    """Track client creation and updates"""
    if created:
        # Client was created
        ClientHistory.objects.create(
            client=instance,
            action='created',
            description=f"Client {instance.get_full_name()} was created"
        )
    else:
        # Client was updated - this will be handled by the serializer
        pass


@receiver(post_delete, sender=Client)
def client_deleted(sender, instance, **kwargs):
    """Track client deletion"""
    # Note: This won't create a history entry since the client is being deleted
    # But we could log this to a separate audit log if needed
    pass


@receiver(post_save, sender=ClientPreference)
def client_preference_saved(sender, instance, created, **kwargs):
    """Track client preference changes"""
    action = 'preference_created' if created else 'preference_updated'
    description = f"Preference {instance.preference_type}:{instance.preference_key} was {'created' if created else 'updated'}"
    
    ClientHistory.objects.create(
        client=instance.client,
        action=action,
        description=description
    )


@receiver(post_delete, sender=ClientPreference)
def client_preference_deleted(sender, instance, **kwargs):
    """Track client preference deletion"""
    ClientHistory.objects.create(
        client=instance.client,
        action='preference_deleted',
        description=f"Preference {instance.preference_type}:{instance.preference_key} was deleted"
    )
