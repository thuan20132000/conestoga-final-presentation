from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from business.models import Business
from simple_history.models import HistoricalRecords


class Client(models.Model):
    """Client information for appointments and services"""
    first_name = models.CharField(max_length=100, help_text="Client's first name")
    last_name = models.CharField(max_length=100, help_text="Client's last name", blank=True, null=True)
    email = models.EmailField(blank=True, null=True, help_text="Primary email address")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Primary phone number")
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of birth for age verification")
    
    # Address information
    address_line1 = models.CharField(max_length=255, blank=True, null=True, help_text="Street address")
    address_line2 = models.CharField(max_length=255, blank=True, null=True, help_text="Apartment, suite, etc.")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City")
    state_province = models.CharField(max_length=100, blank=True, null=True, help_text="State or Province")
    postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="Postal/ZIP code")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="Country")
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True, help_text="Emergency contact full name")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Emergency contact phone")
    emergency_contact_relation = models.CharField(max_length=100, blank=True, null=True, help_text="Relationship to client")
    
    # Client preferences and information
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('sms', 'SMS'),
            ('none', 'No Contact'),
        ],
        default='email',
        help_text="Preferred method of contact"
    )
    notes = models.TextField(blank=True, null=True, help_text="Special notes about the client")
    medical_notes = models.TextField(blank=True, null=True, help_text="Medical conditions or allergies")
    
    # Business relationship
    primary_business = models.ForeignKey(
        Business,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_clients',
        help_text="Primary business this client is associated with"
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True, help_text="Whether the client is active")
    is_vip = models.BooleanField(default=False, help_text="VIP client status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()
    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['email', 'phone', 'primary_business']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        """Return the client's full name"""
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.is_active = True
        super().save(*args, **kwargs)