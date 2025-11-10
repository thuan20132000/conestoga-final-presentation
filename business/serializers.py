from rest_framework import serializers
from django.db.models import Sum, Avg
from .models import (
    BusinessType, Business, OperatingHours, BusinessSettings
)

class BusinessTypeSerializer(serializers.ModelSerializer):
    """Serializer for BusinessType model"""
    
    class Meta:
        model = BusinessType
        fields = ['id', 'name', 'description', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']


class OperatingHoursSerializer(serializers.ModelSerializer):
    """Serializer for OperatingHours model"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = OperatingHours
        fields = [
            'id', 'day_of_week', 'day_name', 'is_open', 'open_time', 
            'close_time', 'is_break_time', 'break_start_time', 'break_end_time',
            'business'
        ]
        read_only_fields = ['id', 'business']


class BusinessSettingsSerializer(serializers.ModelSerializer):
    """Serializer for BusinessSettings model"""
    
    class Meta:
        model = BusinessSettings
        fields = [
            'id', 'advance_booking_days', 'min_advance_booking_hours', 
            'max_advance_booking_days', 'time_slot_interval', 'buffer_time_minutes',
            'send_reminder_emails', 'send_reminder_sms', 'reminder_hours_before',
            'send_confirmation_sms',
            'currency', 'tax_rate', 'require_payment_advance', 'allow_online_booking',
            'require_client_phone', 'require_client_email', 'auto_confirm_appointments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model"""
    
    class Meta:
        model = Business
        fields = ['id', 'name', 'business_type', 'phone_number', 'email', 'website', 'address', 'city', 'state_province', 'postal_code', 'country', 'timezone', 'status', 'description', 'logo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BusinessListSerializer(serializers.ModelSerializer):
    """Simplified serializer for business list views"""
    business_type_name = serializers.CharField(source='business_type.name', read_only=True)
    
    class Meta:
        model = Business
        fields = [
            'id', 'name', 'business_type', 'business_type_name', 'phone_number',
            'email', 'city', 'state_province', 'country', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BusinessDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for business detail views"""
    business_type_name = serializers.CharField(source='business_type.name', read_only=True)
    operating_hours = OperatingHoursSerializer(many=True, read_only=True)
    settings = BusinessSettingsSerializer(read_only=True)
    
    class Meta:
        model = Business
        fields = [
            'id', 'name', 'business_type', 'business_type_name', 'phone_number',
            'email', 'website', 'address', 'city', 'state_province', 'postal_code',
            'country', 'timezone', 'status', 'description', 'logo', 'operating_hours',
            'settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BusinessCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating businesses"""
    operating_hours = OperatingHoursSerializer(many=True, required=False)
    settings = BusinessSettingsSerializer(required=False)
    
    class Meta:
        model = Business
        fields = [
            'name', 'business_type', 'phone_number', 'email', 'website',
            'address', 'city', 'state_province', 'postal_code', 'country',
            'timezone', 'status', 'description', 'logo', 'operating_hours', 'settings'
        ]
    
    def create(self, validated_data):
        operating_hours_data = validated_data.pop('operating_hours', [])
        settings_data = validated_data.pop('settings', {})
        
        business = Business.objects.create(**validated_data)
        
        # Create default operating hours for all days
        if not operating_hours_data:
            for day in range(7):
                OperatingHours.objects.create(
                    business=business,
                    day_of_week=day,
                    is_open=True if day < 5 else False,  # Open weekdays, closed weekends
                    open_time='09:00' if day < 5 else None,
                    close_time='17:00' if day < 5 else None
                )
        else:
            for hours_data in operating_hours_data:
                OperatingHours.objects.create(business=business, **hours_data)
        
        # Create default settings
        BusinessSettings.objects.create(business=business, **settings_data)
        
        return business
    
    def update(self, instance, validated_data):
        operating_hours_data = validated_data.pop('operating_hours', None)
        settings_data = validated_data.pop('settings', None)
        
        # Update business fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update operating hours if provided
        if operating_hours_data is not None:
            instance.operating_hours.all().delete()
            for hours_data in operating_hours_data:
                OperatingHours.objects.create(business=instance, **hours_data)
        
        # Update settings if provided
        if settings_data is not None:
            settings, created = BusinessSettings.objects.get_or_create(business=instance)
            for attr, value in settings_data.items():
                setattr(settings, attr, value)
            settings.save()
        
        return instance


class ReceptionistStatisticsSerializer(serializers.Serializer):
    """Serializer for business receptionist statistics"""
    total_calls = serializers.SerializerMethodField()
    unsuccessful_calls = serializers.SerializerMethodField()
    negative_sentiment_calls = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    average_cost = serializers.SerializerMethodField()
    recent_calls = serializers.SerializerMethodField()
    
    
    def get_total_calls(self, business_calls):
        return business_calls.count()
    
    def get_unsuccessful_calls(self, business_calls):
        return business_calls.filter(outcome='unsuccessful').count()
    
    def get_negative_sentiment_calls(self, business_calls):
        return business_calls.filter(sentiment='negative').count()
    
    def get_total_cost(self, business_calls):
        total_cost = business_calls.aggregate(total_cost=Sum('cost'))['total_cost'] or 0.0
        return round(total_cost, 2)
    
    def get_average_cost(self, business_calls):
        total_cost = self.get_total_cost(business_calls)
        total_calls = self.get_total_calls(business_calls)
        if total_calls > 0:
            return round(total_cost / total_calls, 4)
        return 0.0

    def get_recent_calls(self, business_calls):
        recent_calls = business_calls.order_by('-started_at')[:15]
        return recent_calls.values(
            'id', 
            'started_at', 
            'ended_at', 
            'duration_seconds', 
            'cost', 
            'outcome', 
            'sentiment',
            'direction', 
            'caller_number', 
            'receiver_number', 
            'call_sid', 
            'status', 
            'transcript_summary',
            'conversation_transcript'
        )

class BusinessDashboardSerializer(BusinessDetailSerializer):
    """Serializer for business dashboard"""
    
    class Meta(BusinessDetailSerializer.Meta):
        fields = BusinessDetailSerializer.Meta.fields 
        read_only_fields = BusinessDetailSerializer.Meta.read_only_fields
