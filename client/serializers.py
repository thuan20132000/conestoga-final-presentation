from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='get_age', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    primary_business_name = serializers.CharField(source='primary_business.name', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'date_of_birth', 'age', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country', 'full_address',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'preferred_contact_method', 'notes', 'medical_notes',
            'primary_business', 'primary_business_name', 'is_active', 'is_vip',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """Validate email uniqueness"""
        if value:
            queryset = Client.objects.filter(email=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("A client with this email already exists.")
        return value

    def validate_phone(self, value):
        """Validate phone uniqueness"""
        if value:
            queryset = Client.objects.filter(phone=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("A client with this phone number already exists.")
        return value


class ClientListSerializer(serializers.ModelSerializer):
    """Simplified serializer for client lists"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='get_age', read_only=True)
    primary_business_name = serializers.CharField(source='primary_business.name', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'date_of_birth', 'age', 'primary_business_name', 'is_active',
            'is_vip', 'created_at'
        ]


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new clients"""
    
    class Meta:
        model = Client
        fields = '__all__'
    
    def create(self, validated_data):
        """Create client with business"""
        try:
            client = Client.objects.create(**validated_data)
            return client
        except Exception as e:
            raise serializers.ValidationError(str(e))

class ClientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing clients"""
    
    class Meta:
        model = Client
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class ClientStatsSerializer(serializers.Serializer):
    """Serializer for client statistics"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    vip_clients = serializers.IntegerField()
    new_clients_this_month = serializers.IntegerField()
    clients_by_business = serializers.DictField()
    clients_by_preferred_contact = serializers.DictField()
