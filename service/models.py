from django.db import models
from business.models import Business


class ServiceCategory(models.Model):
    """Categories for organizing services (e.g., Hair Services, Nail Services, etc.)"""
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='service_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_online_booking = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = ['business', 'name']
        verbose_name_plural = 'Service Categories'
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"


class Service(models.Model):
    """Services offered by the business"""
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in local currency")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    requires_staff = models.BooleanField(default=True)
    max_capacity = models.PositiveIntegerField(default=1, help_text="Maximum number of clients for this service")
    is_online_booking = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = ['business', 'name']
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"