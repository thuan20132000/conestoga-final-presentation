from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Staff, StaffService, StaffRole, StaffWorkingHours, StaffOffDay


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
            'hire_date', 'bio', 'photo',
            'business',
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

class StaffWorkingHoursSerializer(serializers.ModelSerializer):
    """Serializer for StaffWorkingHours model"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    class Meta:
        model = StaffWorkingHours
        fields = '__all__'

class StaffWorkingHoursCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating staff working hours"""
    class Meta:
        model = StaffWorkingHours
        fields = ['day_of_week', 'start_time', 'end_time', 'is_working']

class StaffOffDaySerializer(serializers.ModelSerializer):
    """Serializer for StaffOffDay model"""
    class Meta:
        model = StaffOffDay
        fields = '__all__'

class StaffOffDayCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating staff off days"""
    class Meta:
        model = StaffOffDay
        fields = ['start_date', 'end_date', 'reason', 'staff']


class StaffCalendarSerializer(StaffSerializer):
    """Serializer for staff calendar"""
    working_hours = serializers.SerializerMethodField()
    class Meta:
        model = Staff
        fields = StaffSerializer.Meta.fields + ['working_hours']
        
    def get_working_hours(self, obj):
        """Get working hours for staff"""
        try:    
            weekday = self.context.get('weekday')
            working_hours = obj.working_hours.filter(day_of_week=weekday).first()
            return StaffWorkingHoursSerializer(working_hours).data
        except Exception as e:
            return None


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "username" and "password".')
        
        return attrs


class UserProfileSerializer(StaffSerializer):
    """Serializer for authenticated user profile"""
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta(StaffSerializer.Meta):
        fields = [
            'id', 
            'username',
            'first_name', 
            'last_name', 
            'full_name', 
            'email', 
            'phone',
            'role',
            'role_name',
            'business',
            'business_name',
            'is_active',
            'is_online_booking_allowed', 
            'is_payment_processing_allowed',
            'hire_date', 
            'bio', 
            'photo',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']