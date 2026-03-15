from django.db import models
import uuid
from main.models import SoftDeleteModel
from django.utils import timezone

class BusinessType(SoftDeleteModel):
    """Different types of businesses that can use the system."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # For UI icons
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Business(SoftDeleteModel):
    """Represents a salon or company using the AI receptionist."""
    BUSINESS_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Approval'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('CAD', 'CAD'),
        ('EUR', 'EUR'),
        ('GBP', 'GBP'),
        ('JPY', 'JPY'),
        ('AUD', 'AUD'),
        ('NZD', 'NZD'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    business_type = models.ForeignKey(BusinessType, on_delete=models.PROTECT, related_name='businesses')
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    twilio_phone_number = models.CharField(max_length=50, blank=True, null=True)
    google_review_url = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default="Canada")
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default="CAD")
    cost_per_minute = models.DecimalField(max_digits=10, decimal_places=2, default=0.5)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=BUSINESS_STATUS_CHOICES, default="active")
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Businesses'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
class OperatingHours(SoftDeleteModel):
    """Operating hours for each day of the week"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='operating_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    is_break_time = models.BooleanField(default=False, help_text="Has break time during the day")
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['business', 'day_of_week']
        ordering = ['day_of_week']
    
    def __str__(self):
        day_name = dict(self.DAY_CHOICES)[self.day_of_week]
        if not self.is_open:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time} - {self.close_time}"


class BusinessSettings(SoftDeleteModel):
    TIMEZONE_CHOICES = [
        ('America/Toronto', 'America/Toronto'),
        ('America/New_York', 'America/New_York'),
        ('America/Los_Angeles', 'America/Los_Angeles'),
        ('America/Chicago', 'America/Chicago'),
        ('America/Phoenix', 'America/Phoenix'),
    ]
        
    """Additional settings and preferences for the business"""
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='settings')
    
    # Timezone settings
    timezone = models.CharField(max_length=100, choices=TIMEZONE_CHOICES, default="America/Toronto")
    
    # Booking settings
    advance_booking_days = models.PositiveIntegerField(default=30, help_text="How many days in advance can clients book")
    min_advance_booking_hours = models.PositiveIntegerField(default=2, help_text="Minimum hours in advance for booking")
    max_advance_booking_days = models.PositiveIntegerField(default=90, help_text="Maximum days in advance for booking")
    
    # Time slot settings
    time_slot_interval = models.PositiveIntegerField(default=15, help_text="Time slot interval in minutes")
    buffer_time_minutes = models.PositiveIntegerField(default=0, help_text="Buffer time between appointments")
    
    # Notification settings
    send_reminder_emails = models.BooleanField(default=True)
    send_reminder_sms = models.BooleanField(default=False)
    reminder_hours_before = models.PositiveIntegerField(default=24, help_text="Hours before appointment to send reminder")
    send_confirmation_sms = models.BooleanField(default=False)
    send_cancellation_sms = models.BooleanField(default=False)
    
    # Payment settings
    currency = models.CharField(max_length=3, default="CAD")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.13, help_text="Tax rate as decimal (0.13 = 13%)")
    require_payment_advance = models.BooleanField(default=False)
    
    # General settings
    allow_online_booking = models.BooleanField(default=True)
    require_client_phone = models.BooleanField(default=True)
    require_client_email = models.BooleanField(default=False)
    auto_confirm_appointments = models.BooleanField(default=False)
    
    # Gift card settings
    allow_online_gift_cards = models.BooleanField(default=False)
    
    gift_card_processing_fee_enabled = models.BooleanField(default=True)
    
    tax_with_cash_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Settings for {self.business.name}"

class BusinessRoles(SoftDeleteModel):
    """Roles for the business"""
    ROLE_CHOICES = [
        ('Owner', 'Owner'),
        ('Manager', 'Manager'),
        ('Stylist', 'Stylist'),
        ('Technician', 'Technician'),
        ('Assistant', 'Assistant'),
        ('Receptionist', 'Receptionist'),
        ('Other', 'Other'),
    ]
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100, choices=ROLE_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"
    
    def is_managers(self):
        return self.name in ['Manager', 'Owner', 'Receptionist']
class BusinessOnlineBooking(SoftDeleteModel):
    """Online booking configuration for the business"""
    business = models.OneToOneField(
        Business, 
        on_delete=models.CASCADE, 
        related_name='online_booking',
        help_text="The business this online booking page belongs to"
    )
    name = models.CharField(max_length=255, help_text="Name of the online booking page")
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="URL-friendly identifier for the booking page"
    )
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True, help_text="Description shown on the booking page")
    policy = models.TextField(blank=True, null=True, help_text="Booking policy/terms shown to clients")
    
    # Booking settings
    interval_minutes = models.PositiveIntegerField(
        default=15, 
        help_text="Time slot interval in minutes"
    )
    buffer_time_minutes = models.PositiveIntegerField(
        default=0, 
        help_text="Buffer time between appointments in minutes"
    )
    
    # Status and visibility
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether the online booking page is active and accessible"
    )
    
    # Shareable link
    shareable_link = models.URLField(
        blank=True, 
        null=True,
        help_text="Shareable URL for the online booking page"
    )
    
    class Meta:
        ordering = ['business__name', 'name']
        verbose_name = 'Online Booking'
        verbose_name_plural = 'Online Bookings'
    
    def __str__(self):
        return f"{self.business.name} - {self.name or 'Online Booking'}"
    
    def save(self, *args, **kwargs):
        """Save the online booking configuration"""
        # Generate slug from name if not provided
        if not self.slug and self.name:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Check for existing slugs, excluding current instance if it exists
            queryset = BusinessOnlineBooking.objects.filter(slug=slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            while queryset.exists():
                slug = f"{base_slug}-{counter}"
                queryset = BusinessOnlineBooking.objects.filter(slug=slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)
                counter += 1
            self.slug = slug
        
        super().save(*args, **kwargs)

class BusinessBanner(SoftDeleteModel):
    BANNER_TYPE_CHOICES = [
        ('promotion', 'Promotion'),
        ('info', 'Information'),
        ('alert', 'Alert'),
    ]
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, related_name='banners')
    type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES, default='info')
    title = models.CharField(max_length=120)
    message = models.TextField()
    cta_text = models.CharField(max_length=50, blank=True, null=True)
    cta_url = models.CharField(max_length=255, blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)

    dismissible = models.BooleanField(default=True)

    # Styling (optional but useful)
    background_color = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="HEX or Tailwind class"
    )

    text_color = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "is_active"]),
        ]

    def __str__(self):
        return f"{self.business} | {self.title}"

    def is_visible(self):
        """
        Check if banner should be shown right now
        """
        now = timezone.now()

        if not self.is_active:
            return False

        if self.start_at and self.start_at > now:
            return False

        if self.end_at and self.end_at < now:
            return False

        return True