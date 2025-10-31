from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import ServiceCategory, Service
from .serializers import (
    ServiceCategorySerializer, ServiceSerializer, ServiceCreateUpdateSerializer
)
from business.models import Business
from main.viewsets import BaseModelViewSet


class ServiceCategoryViewSet(BaseModelViewSet):
    """ViewSet for ServiceCategory management"""
    queryset = ServiceCategory.objects.select_related('business')
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, pk=None):
        """Get services for a category"""
        category = self.get_object()
        services = category.services.all()
        serializer = ServiceSerializer(services, many=True)
        return self.response_success(serializer.data, message="Services retrieved successfully")

class ServiceViewSet(BaseModelViewSet):
    """ViewSet for Service management"""
    queryset = Service.objects.select_related('business', 'category')
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get services grouped by category"""
        business_id = request.query_params.get('business')
        if not business_id:
            return Response(
                {'error': 'business parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            return Response(
                {'error': 'Business not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        categories = business.service_categories.filter(is_active=True).prefetch_related('services')
        result = []
        
        for category in categories:
            services = category.services.filter(is_active=True)
            category_data = ServiceCategorySerializer(category).data
            category_data['services'] = ServiceSerializer(services, many=True).data
            result.append(category_data)
        
        return Response(result)