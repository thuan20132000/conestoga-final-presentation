from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from .models import ServiceCategory, Service
from .serializers import (
    ServiceCategorySerializer, ServiceSerializer, CalendarServiceCategorySerializer
)
from main.viewsets import BaseModelViewSet


class ServiceCategoryFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(field_name='is_active')
    business_id = filters.NumberFilter(field_name='business_id')
    class Meta:
        model = ServiceCategory
        fields = ['is_active', 'business_id']

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
    
    @action(detail=False, methods=['get'], url_path='calendar-services')
    def calendar_services(self, request):
        """Get calendar services"""
        try:
            queryset = ServiceCategory.objects.filter(is_active=True).order_by('sort_order')
            serializer = CalendarServiceCategorySerializer(queryset, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
    

class ServiceFilter(filters.FilterSet):
    business_id = filters.NumberFilter(field_name='business_id')
    category_id = filters.NumberFilter(field_name='category_id')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    description = filters.CharFilter(field_name='description', lookup_expr='icontains')
    is_active = filters.BooleanFilter(field_name='is_active')
    class Meta:
        model = Service
        fields = ['business_id', 'category_id', 'name', 'description', 'is_active']

class ServiceViewSet(BaseModelViewSet):
    """ViewSet for Service management"""
    queryset = Service.objects.select_related('business', 'category')
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ServiceFilter
    
    def get_queryset(self):
        """Get queryset for services"""
        queryset = super().get_queryset()
        return queryset
    
