from rest_framework import serializers
from .models import Staff, StaffService


class StaffServiceSerializer(serializers.ModelSerializer):
    """Serializer for StaffService model"""
    service_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffService
        fields = ['id', 'service_id', 'service_name', 'is_primary', 'created_at']
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
    staff_services = StaffServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'role', 'is_active', 'hire_date', 'bio', 'photo', 'staff_services',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating staff"""
    
    class Meta:
        model = Staff
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'role',
            'is_active', 'hire_date', 'bio', 'photo'
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
