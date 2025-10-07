from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Client(models.Model):
    """Client information for appointments"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True,
                             help_text="Special notes about the client")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['email', 'phone']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class AppointmentStatus(models.Model):
    """Appointment status definitions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]

    name = models.CharField(max_length=50, choices=STATUS_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Hex color for UI display")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Appointment Statuses'

    def __str__(self):
        return self.get_name_display()


class Appointment(models.Model):
    """Main appointment model"""
    business = models.ForeignKey(
        'business.Business', on_delete=models.CASCADE, related_name='appointments')
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(
        'service.Service', on_delete=models.CASCADE, related_name='appointments')
    staff = models.ForeignKey(
        'staff.Staff', on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)

    # Appointment timing
    appointment_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration in minutes", null=True, blank=True)

    # Status and tracking
    status = models.ForeignKey(
        AppointmentStatus, on_delete=models.PROTECT, related_name='appointments')
    notes = models.TextField(blank=True, null=True,
                             help_text="Appointment notes")
    internal_notes = models.TextField(
        blank=True, null=True, help_text="Internal notes (not visible to client)")

    # Pricing
    service_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at time of booking", null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price including tax", null=True, blank=True)

    # Payment tracking
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True,
                                      choices=[
                                          ('cash', 'Cash'),
                                          ('credit_card', 'Credit Card'),
                                          ('debit_card', 'Debit Card'),
                                          ('bank_transfer', 'Bank Transfer'),
                                          ('online', 'Online Payment'),
                                          ('other', 'Other'),
                                      ])
    payment_notes = models.TextField(blank=True, null=True)

    # Booking tracking
    booked_by = models.ForeignKey('staff.Staff', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='booked_appointments')
    booking_source = models.CharField(max_length=50, default='online',
                                      choices=[
                                          ('online', 'Online Booking'),
                                          ('phone', 'Phone Booking'),
                                          ('walk_in', 'Walk-in'),
                                          ('staff', 'Staff Booking'),
                                          ('ai_receptionist', 'AI Receptionist'),
                                      ])

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Recurring appointments
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.CharField(max_length=20, blank=True, null=True,
                                         choices=[
                                             ('weekly', 'Weekly'),
                                             ('biweekly', 'Bi-weekly'),
                                             ('monthly', 'Monthly'),
                                         ])

    recurring_end_date = models.DateField(null=True, blank=True)
    parent_appointment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                           related_name='recurring_appointments')

    class Meta:
        ordering = ['appointment_date', 'start_time']
        unique_together = ['business', 'staff', 'appointment_date', 'start_time']
        indexes = [
            models.Index(fields=['appointment_date', 'start_time']),
            models.Index(fields=['business', 'appointment_date']),
            models.Index(fields=['client']),
            models.Index(fields=['staff', 'appointment_date']),
        ]

    def __str__(self):
        return f"{self.client.get_full_name()} - {self.service.name} on {self.appointment_date} at {self.start_time}"

    def clean(self):
        from django.core.exceptions import ValidationError

        # Validate that end time is after start time
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time")

        # Validate appointment date is not in the past
        if self.appointment_date and self.appointment_date < timezone.now().date():
            raise ValidationError("Appointment date cannot be in the past")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_past(self):
        """Check if appointment is in the past"""
        now = timezone.now()
        appointment_datetime = timezone.datetime.combine(
            self.appointment_date,
            self.end_time
        )
        return appointment_datetime < now

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
        return self.status.color if self.status else "#6c757d"


class AppointmentService(models.Model):
    """Appointment service model"""
    
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='appointment_services')
    service = models.ForeignKey(
        'service.Service', on_delete=models.CASCADE, related_name='appointment_services')
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointment_services'
    )
    is_requested = models.BooleanField(default=False)
    custom_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    custom_duration = models.IntegerField(
        help_text="Duration in minutes", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration in minutes", null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['appointment', 'service']

    def __str__(self):
        return f"{self.appointment} - {self.service.name}"

    def save(self, *args, **kwargs):
        if not self.custom_duration:
            self.custom_duration = self.service.duration_minutes
        if not self.custom_price:
            self.custom_price = self.service.price
        super().save(*args, **kwargs)

class AppointmentReminder(models.Model):
    """Track appointment reminders sent to clients"""
    REMINDER_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    scheduled_time = models.DateTimeField(
        help_text="When the reminder was scheduled to be sent")
    sent_time = models.DateTimeField(
        null=True, blank=True, help_text="When the reminder was actually sent")
    is_sent = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    delivery_status = models.CharField(max_length=50, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']

    def __str__(self):
        return f"{self.appointment} - {self.get_reminder_type_display()} reminder"


class AppointmentConflict(models.Model):
    """Track appointment scheduling conflicts"""
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='conflicts')
    conflicting_appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE,
                                                related_name='conflicts_as_conflicting')
    conflict_type = models.CharField(max_length=50,
                                     choices=[
                                         ('staff_double_booking',
                                          'Staff Double Booking'),
                                         ('time_overlap', 'Time Overlap'),
                                         ('resource_conflict',
                                          'Resource Conflict'),
                                     ])
    description = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        unique_together = ['appointment', 'conflicting_appointment']

    def __str__(self):
        return f"Conflict: {self.appointment} vs {self.conflicting_appointment}"
