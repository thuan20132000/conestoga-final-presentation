from rest_framework import serializers
from .models import Staff, StaffService, StaffRole


class StaffRoleSerializer(serializers.ModelSerializer):
    """Serializer for StaffRole model"""
    class Meta:
        model = StaffRole
        fields = ['id', 'name', 'description']

class StaffServiceSerializer(serializers.ModelSerializer):
    """Serializer for StaffService model"""
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffService
        fields = ['id', 'service_id', 'service_name', 'is_primary', 'is_online_booking_allowed', 'is_payment_processing_allowed', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_service_name(self, obj):
        try:
            from service.models import Service
            service = Service.objects.get(id=obj.service_id)
            return service.name
        except:
            return f"Service {obj.service_id}"


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for Staff model"""
    full_name = serializers.CharField(read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    class Meta:
        model = Staff
        fields = [
            'id', 
            'first_name', 
            'last_name', 
            'full_name', 'email', 'phone',
            'role','role_name', 
            'is_active',
            'is_online_booking_allowed', 
            'is_payment_processing_allowed',
            'hire_date', 'bio', 'photo',
            'staff_salary_settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating staff"""
    
    class Meta:
        model = Staff
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'role',
            'is_active',
            'is_online_booking_allowed',
            'is_payment_processing_allowed',
            'hire_date', 'bio', 'photo'
        ]
    
    def validate_email(self, value):
        if value:
            business = self.context.get('business')
            if business and Staff.objects.filter(
                business=business, email=value
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise serializers.ValidationError(
                    "A staff member with this email already exists for this business."
                )
        return value
