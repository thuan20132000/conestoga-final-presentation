from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import (
    BusinessType, Business, OperatingHours, BusinessSettings
)
from .serializers import (
    BusinessTypeSerializer, BusinessListSerializer, BusinessDetailSerializer,
    BusinessCreateUpdateSerializer, OperatingHoursSerializer, BusinessSettingsSerializer
)


class BusinessTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for BusinessType - read-only since these are predefined"""
    queryset = BusinessType.objects.all()
    serializer_class = BusinessTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class BusinessViewSet(viewsets.ModelViewSet):
    """ViewSet for Business management"""
    queryset = Business.objects.select_related('business_type').prefetch_related(
        'operating_hours', 'settings'
    )
    permission_classes = [AllowAny]  # Adjust based on your authentication needs
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_type', 'status', 'city', 'state_province', 'country']
    search_fields = ['name', 'description', 'address', 'city']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BusinessListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BusinessCreateUpdateSerializer
        return BusinessDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by business type if specified
        business_type = self.request.query_params.get('business_type')
        if business_type:
            queryset = queryset.filter(business_type__name__icontains=business_type)
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(
                Q(city__icontains=location) | 
                Q(state_province__icontains=location) |
                Q(address__icontains=location)
            )
        
        return queryset
    
    
    @action(detail=True, methods=['get'])
    def operating_hours(self, request, pk=None):
        """Get operating hours for a specific business"""
        business = self.get_object()
        hours = business.operating_hours.all()
        serializer = OperatingHoursSerializer(hours, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def settings(self, request, pk=None):
        """Get or update business settings"""
        business = self.get_object()
        
        if request.method == 'GET':
            settings, created = BusinessSettings.objects.get_or_create(business=business)
            serializer = BusinessSettingsSerializer(settings)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            settings, created = BusinessSettings.objects.get_or_create(business=business)
            serializer = BusinessSettingsSerializer(
                settings, data=request.data, partial=request.method == 'PATCH'
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class OperatingHoursViewSet(viewsets.ModelViewSet):
    """ViewSet for OperatingHours management"""
    queryset = OperatingHours.objects.select_related('business')
    serializer_class = OperatingHoursSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business', 'day_of_week', 'is_open']
    ordering_fields = ['day_of_week']
    ordering = ['day_of_week']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by business if specified
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        return queryset
