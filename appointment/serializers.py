from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Appointment, AppointmentStatus, AppointmentReminder, AppointmentConflict, AppointmentService
from client.models import Client
from business.models import Business
from service.models import Service
from staff.models import Staff


class AppointmentStatusSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentStatus model"""
    
    class Meta:
        model = AppointmentStatus
        fields = [
            'id', 'name', 'description', 'color', 'is_active', 'sort_order'
        ]
        read_only_fields = ['id']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    status_name = serializers.CharField(source='status.get_name_display', read_only=True)
    status_color = serializers.CharField(source='status.color', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'business', 'business_name', 'client', 'client_name', 'service', 'service_name',
            'staff', 'staff_name', 'appointment_date', 'start_time', 'end_time', 'duration_minutes',
            'status', 'status_name', 'status_color', 'notes', 'internal_notes', 'service_price',
            'tax_amount', 'total_price', 'is_paid', 'payment_method', 'payment_notes',
            'booked_by', 'booking_source', 'created_at', 'updated_at', 'confirmed_at',
            'completed_at', 'cancelled_at', 'is_recurring', 'recurring_pattern',
            'recurring_end_date', 'parent_appointment', 'is_past', 'is_today', 'is_upcoming'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at',
            'is_past', 'is_today', 'is_upcoming'
        ]
    
    def validate_appointment_date(self, value):
        """Validate appointment date"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Appointment date cannot be in the past")
        return value
    
    def validate(self, data):
        """Validate appointment data"""
        # Check if end time is after start time
        if data.get('start_time') and data.get('end_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        # Check for staff availability if staff is assigned
        if data.get('staff') and data.get('appointment_date') and data.get('start_time') and data.get('end_time'):
            self._validate_staff_availability(data)
        
        # Calculate total price if not provided
        if not data.get('total_price') and data.get('service_price'):
            tax_rate = data.get('business').settings.tax_rate if data.get('business') else 0
            tax_amount = data['service_price'] * tax_rate
            data['tax_amount'] = tax_amount
            data['total_price'] = data['service_price'] + tax_amount
        
        return data
    
    def _validate_staff_availability(self, data):
        """Validate staff availability for the appointment time"""
        staff = data['staff']
        appointment_date = data['appointment_date']
        start_time = data['start_time']
        end_time = data['end_time']
        
        # Check for existing appointments for this staff member
        existing_appointments = Appointment.objects.filter(
            staff=staff,
            appointment_date=appointment_date,
            status__name__in=['scheduled', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)
        
        for appointment in existing_appointments:
            # Check for time overlap
            if (start_time < appointment.end_time and end_time > appointment.start_time):
                raise serializers.ValidationError(
                    f"Staff member {staff.get_full_name()} has a conflicting appointment "
                    f"from {appointment.start_time} to {appointment.end_time}"
                )
    
    def create(self, validated_data):
        """Create appointment with automatic status setting"""
        # Set default status if not provided
        if not validated_data.get('status'):
            default_status = AppointmentStatus.objects.filter(name='scheduled').first()
            if default_status:
                validated_data['status'] = default_status
        
        appointment = super().create(validated_data)
        
        # Set confirmed_at if status is confirmed
        if appointment.status.name == 'confirmed':
            appointment.confirmed_at = timezone.now()
            appointment.save()
        
        return appointment


class AppointmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for appointment lists"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    status_name = serializers.CharField(source='status.get_name_display', read_only=True)
    status_color = serializers.CharField(source='status.color', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'client_name', 'service_name', 'staff_name', 'appointment_date',
            'start_time', 'end_time', 'status_name', 'status_color', 'total_price',
            'is_paid', 'created_at'
        ]


class AppointmentAvailabilitySerializer(serializers.Serializer):
    """Serializer for checking appointment availability"""
    business = serializers.PrimaryKeyRelatedField(queryset=Business.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    appointment_date = serializers.DateField()
    staff = serializers.PrimaryKeyRelatedField(
        queryset=Staff.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    def validate_appointment_date(self, value):
        """Validate appointment date"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the past")
        return value
    
    def validate(self, data):
        """Validate availability data"""
        business = data['business']
        service = data['service']
        appointment_date = data['appointment_date']
        staff = data.get('staff')
        
        # Check if business is open on this date
        day_of_week = appointment_date.weekday()
        operating_hours = business.operating_hours.filter(day_of_week=day_of_week).first()
        
        if not operating_hours or not operating_hours.is_open:
            raise serializers.ValidationError("Business is closed on this date")
        
        return data


class AppointmentReminderSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentReminder model"""
    
    class Meta:
        model = AppointmentReminder
        fields = [
            'id', 'appointment', 'reminder_type', 'scheduled_time', 'sent_time',
            'is_sent', 'is_delivered', 'delivery_status', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AppointmentConflictSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentConflict model"""
    appointment_str = serializers.CharField(source='appointment.__str__', read_only=True)
    conflicting_appointment_str = serializers.CharField(source='conflicting_appointment.__str__', read_only=True)
    
    class Meta:
        model = AppointmentConflict
        fields = [
            'id', 'appointment', 'appointment_str', 'conflicting_appointment',
            'conflicting_appointment_str', 'conflict_type', 'description',
            'is_resolved', 'resolved_at', 'resolved_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AppointmentServiceSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentService model"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    
    class Meta:
        model = AppointmentService
        fields = [
            'id', 'appointment', 'service', 'service_name', 'staff', 'staff_name',
            'is_requested', 'custom_price', 'custom_duration', 'is_active',
            'start_time', 'end_time', 'duration_minutes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AppointmentStatsSerializer(serializers.Serializer):
    """Serializer for appointment statistics"""
    total_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    today_appointments = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_appointment_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    no_show_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
