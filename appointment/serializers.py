from rest_framework import serializers
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Appointment, AppointmentService
from client.models import Client
from business.models import Business
from service.models import Service
from staff.models import Staff


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 
            'business', 
            'business_name', 
            'client', 
            'client_name', 
            'client_email',
            'client_phone',
            'appointment_date', 
            'status', 
            'notes', 
            'internal_notes', 
            'booked_by', 
            'booking_source', 
            'created_at', 
            'updated_at',
            'confirmed_at',
            'completed_at', 
            'cancelled_at',
            'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at', 'is_active']
    
    def validate(self, data):
        """Validate appointment data"""
        return data
    
class AppointmentUpdateSerializer(AppointmentSerializer):
    """Serializer for creating appointments"""
    class Meta:
        model = Appointment
        fields = [
            'business', 'client', 'appointment_date', 'status', 'notes', 'internal_notes', 'booked_by', 'booking_source', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at']
        extra_kwargs = {
            'client': {'required': True},
            'appointment_date': {'required': True},
            'status': {'required': True},
        }
    def validate(self, data):
        """Validate appointment data"""
        return data
    
    
    def update(self, instance, validated_data):
        """Update appointment with automatic status setting"""
        try:
            appointment = super().update(instance, validated_data)
            print("updated appointment", appointment)
            return AppointmentDetailSerializer(appointment).data
        except Exception as e:
            raise serializers.ValidationError(str(e))

class AppointmentCreateSerializer(AppointmentSerializer):
    """Serializer for creating appointments"""
    class Meta:
        model = Appointment
        fields = '__all__'

    def create(self, validated_data):
        """Create appointment with automatic status setting"""
        appointment = super().create(validated_data)
        return AppointmentDetailSerializer(appointment).data
class AppointmentServiceSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentService model"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_duration = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    service_price = serializers.DecimalField(source='service.price', read_only=True, max_digits=10, decimal_places=2)
    service_color_code = serializers.CharField(source='service.color_code', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    class Meta:
        model = AppointmentService
        fields = [
            'id', 
            'appointment', 
            'service', 
            'service_name', 
            'service_duration',
            'service_price',
            'service_color_code',
            'staff', 
            'staff_name',
            'is_staff_request', 
            'custom_price', 
            'custom_duration', 
            'start_at', 
            'end_at',
            'created_at', 
            'updated_at',
            'is_active'
        ]
        read_only_fields = ['id', 'created_at']



class AppointmentListSerializer(AppointmentSerializer):
    """Simplified serializer for appointment lists"""
    
    appointment_services = AppointmentServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 
            'client_name', 
            'business_name', 
            'appointment_date',
            'status', 
            'notes', 
            'internal_notes', 
            'booked_by', 
            'booking_source', 
            'is_active',
            'created_at', 
            'updated_at',
            'confirmed_at',
            'completed_at', 
            'cancelled_at',
            'appointment_services'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'confirmed_at', 'completed_at', 'cancelled_at']
        extra_kwargs = {
            'client_name': {'read_only': True},
            'business_name': {'read_only': True},
        }


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

class AppointmentDetailSerializer(AppointmentSerializer):
    """Serializer for detail view of appointment"""
    appointment_services = AppointmentServiceSerializer(many=True, read_only=True)
    start_at = serializers.DateTimeField(source='appointment_services.first.start_at', read_only=True)
    class Meta(AppointmentSerializer.Meta):
        
        fields = AppointmentSerializer.Meta.fields + [
            'start_at',
            'appointment_services',
        ]
        read_only_fields = AppointmentSerializer.Meta.read_only_fields + ['start_at']

