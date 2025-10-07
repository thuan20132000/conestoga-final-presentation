from rest_framework import serializers
from django.utils import timezone
from .models import Client, ClientHistory, ClientPreference
from business.models import Business


class ClientPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for ClientPreference model"""
    
    class Meta:
        model = ClientPreference
        fields = [
            'id', 'preference_type', 'preference_key', 'preference_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientHistorySerializer(serializers.ModelSerializer):
    """Serializer for ClientHistory model"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClientHistory
        fields = [
            'id', 'action', 'description', 'changed_by_name',
            'changed_at'
        ]
        read_only_fields = ['id', 'changed_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='get_age', read_only=True)
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    primary_business_name = serializers.CharField(source='primary_business.name', read_only=True)
    preferences = ClientPreferenceSerializer(many=True, read_only=True)
    history = ClientHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'date_of_birth', 'age', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country', 'full_address',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'preferred_contact_method', 'notes', 'medical_notes',
            'primary_business', 'primary_business_name', 'is_active', 'is_vip',
            'preferences', 'history', 'created_at', 'updated_at'
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
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation',
            'preferred_contact_method', 'notes', 'medical_notes',
            'primary_business', 'is_active', 'is_vip'
        ]

    def create(self, validated_data):
        """Create client with history tracking"""
        client = Client.objects.create(**validated_data)
        
        # Create history entry
        ClientHistory.objects.create(
            client=client,
            action='created',
            description=f"Client {client.get_full_name()} was created",
            changed_by=self.context.get('request').user if self.context.get('request') else None
        )
        
        return client


class ClientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing clients"""
    
    class Meta:
        model = Client
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation',
            'preferred_contact_method', 'notes', 'medical_notes',
            'primary_business', 'is_active', 'is_vip'
        ]

    def update(self, instance, validated_data):
        """Update client with history tracking"""
        # Track changes
        changes = []
        for field, value in validated_data.items():
            if getattr(instance, field) != value:
                old_value = getattr(instance, field)
                changes.append(f"{field}: {old_value} → {value}")
        
        # Update the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Create history entry if there were changes
        if changes:
            ClientHistory.objects.create(
                client=instance,
                action='updated',
                description=f"Updated: {', '.join(changes)}",
                changed_by=self.context.get('request').user if self.context.get('request') else None
            )
        
        return instance


class ClientStatsSerializer(serializers.Serializer):
    """Serializer for client statistics"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    vip_clients = serializers.IntegerField()
    new_clients_this_month = serializers.IntegerField()
    clients_by_business = serializers.DictField()
    clients_by_preferred_contact = serializers.DictField()
