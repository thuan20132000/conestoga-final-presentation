from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Appointment(models.Model):
    """Main appointment model"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    
    BOOKING_SOURCE_CHOICES = [
        ('online', 'Online Booking'),
        ('phone', 'Phone Booking'),
        ('walk_in', 'Walk-in'),
        ('staff', 'Staff Booking'),
        ('ai_receptionist', 'AI Receptionist'),
    ]
    
    # Related entities
    business = models.ForeignKey(
        'business.Business', 
        on_delete=models.SET_NULL, 
        related_name='appointments',
        null=True,
        blank=True
    )
    
    client = models.ForeignKey(
        'client.Client', 
        on_delete=models.SET_NULL, 
        related_name='appointments', 
        null=True, 
        blank=True
    )

    # Appointment timing
    appointment_date = models.DateField()

    # Status and tracking
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True, help_text="Appointment notes")
    internal_notes = models.TextField(blank=True, null=True, help_text="Internal notes (not visible to client)")

    # Booking tracking
    booked_by = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='booked_appointments'
    )
    booking_source = models.CharField(max_length=50, choices=BOOKING_SOURCE_CHOICES, default='online')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['appointment_date','created_at']

    def __str__(self):
        return f"{self.client} - {self.appointment_date}"

    @property
    def is_past(self):
        """Check if appointment is in the past"""
        return self.appointment_date < timezone.now().date()

    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_date == timezone.now().date()

    @property
    def is_upcoming(self):
        """Check if appointment is in the future"""
        return not self.is_past

    def get_status_display_color(self):
        """Get the color for status display"""
        return self.status

    

class AppointmentService(models.Model):
    """Appointment service model"""
    SERVICE_REQUEST_STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.SET_NULL, 
        related_name='appointment_services',
        null=True,
        blank=True
    )
    service = models.ForeignKey(
        'service.Service', 
        on_delete=models.SET_NULL, 
        related_name='appointment_services',
        null=True,
        blank=True
    )
    
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointment_services'
    )
    
    is_staff_request = models.BooleanField(default=False)
    
    custom_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
    )
    
    custom_duration = models.IntegerField(
        help_text="Duration in minutes", 
        null=True, 
        blank=True,
    )
    
    start_at = models.DateTimeField(null=True, blank=True, help_text="Start time for the service")
    end_at = models.DateTimeField(null=True, blank=True, help_text="End time for the service")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_at']

    def __str__(self):
        return f"{self.appointment} - {self.service.name} - {self.start_at} - {self.end_at}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

