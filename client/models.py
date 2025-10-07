from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from business.models import Business


class Client(models.Model):
    """Client information for appointments and services"""
    first_name = models.CharField(max_length=100, help_text="Client's first name")
    last_name = models.CharField(max_length=100, help_text="Client's last name")
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

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['email', 'phone']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        """Return the client's full name"""
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        """Return the client's age based on date of birth"""
        if not self.date_of_birth:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def get_full_address(self):
        """Return formatted full address"""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state_province:
            address_parts.append(self.state_province)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ', '.join(address_parts)

    @property
    def full_name(self):
        """Property for full name"""
        return self.get_full_name()

    @property
    def age(self):
        """Property for age"""
        return self.get_age()


class ClientHistory(models.Model):
    """Track changes and history for clients"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50, help_text="Action performed (created, updated, etc.)")
    description = models.TextField(help_text="Description of the change")
    changed_by = models.ForeignKey('staff.Staff', on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Client History'
        verbose_name_plural = 'Client Histories'

    def __str__(self):
        return f"{self.client} - {self.action} at {self.changed_at}"


class ClientPreference(models.Model):
    """Store client preferences for services and appointments"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='preferences')
    preference_type = models.CharField(
        max_length=50,
        choices=[
            ('service', 'Service Preference'),
            ('staff', 'Staff Preference'),
            ('time', 'Time Preference'),
            ('communication', 'Communication Preference'),
            ('other', 'Other'),
        ]
    )
    preference_key = models.CharField(max_length=100, help_text="Key for the preference")
    preference_value = models.TextField(help_text="Value of the preference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['client', 'preference_type', 'preference_key']
        verbose_name = 'Client Preference'
        verbose_name_plural = 'Client Preferences'

    def __str__(self):
        return f"{self.client} - {self.preference_type}: {self.preference_key}"