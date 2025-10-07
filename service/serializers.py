from rest_framework import serializers
from .models import ServiceCategory, Service


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for ServiceCategory model"""
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'description', 'sort_order', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'category', 'category_name', 'name', 'description', 
            'duration_minutes', 'price', 'is_active', 'requires_staff', 
            'max_capacity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating services"""
    
    class Meta:
        model = Service
        fields = [
            'category', 'name', 'description', 'duration_minutes', 'price',
            'is_active', 'requires_staff', 'max_capacity'
        ]
    
    def validate(self, data):
        # Ensure the category belongs to the same business
        if 'category' in data:
            category = data['category']
            business = self.context.get('business')
            if business and category.business != business:
                raise serializers.ValidationError(
                    "Service category must belong to the same business."
                )
        return data
