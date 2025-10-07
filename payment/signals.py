from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, PaymentTransaction, PaymentStatus


@receiver(post_save, sender=Payment)
def create_payment_transaction(sender, instance, created, **kwargs):
    """Create transaction log when payment status changes"""
    if created:
        # Payment was just created
        PaymentTransaction.objects.create(
            payment=instance,
            event_type='payment_initiated',
            new_status=instance.status,
            amount=instance.amount,
            description=f"Payment initiated for {instance.client.get_full_name()}",
            created_by=instance.processed_by
        )
    else:
        # Check if status changed
        if instance.pk:
            try:
                old_payment = Payment.objects.get(pk=instance.pk)
                if old_payment.status != instance.status:
                    PaymentTransaction.objects.create(
                        payment=instance,
                        event_type='status_changed',
                        previous_status=old_payment.status,
                        new_status=instance.status,
                        description=f"Status changed from {old_payment.status} to {instance.status}",
                        created_by=instance.processed_by
                    )
            except Payment.DoesNotExist:
                pass


@receiver(pre_save, sender=Payment)
def update_payment_timestamps(sender, instance, **kwargs):
    """Update timestamps when payment status changes"""
    if instance.pk:
        try:
            old_payment = Payment.objects.get(pk=instance.pk)
            # Set processed_at when status changes from pending to processing
            if (old_payment.status and old_payment.status.name == 'pending' and
                instance.status and instance.status.name == 'processing' and
                not instance.processed_at):
                instance.processed_at = timezone.now()
        except Payment.DoesNotExist:
            pass
