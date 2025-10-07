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


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceCategory management"""
    serializer_class = ServiceCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['sort_order', 'name', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        queryset = ServiceCategory.objects.select_related('business')
        
        # Filter by business if specified
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        return queryset


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Service management"""
    queryset = Service.objects.select_related('business', 'category')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business', 'category', 'is_active', 'requires_staff']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'duration_minutes', 'created_at']
    ordering = ['category__sort_order', 'name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add business context for validation
        business_id = self.request.query_params.get('business')
        if business_id:
            try:
                context['business'] = Business.objects.get(id=business_id)
            except Business.DoesNotExist:
                pass
        return context
    
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