from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import (
    BusinessType, Business, OperatingHours, BusinessSettings
)
from .serializers import (
    BusinessTypeSerializer, BusinessListSerializer, BusinessDetailSerializer,
    BusinessCreateUpdateSerializer, OperatingHoursSerializer, BusinessSettingsSerializer
)
from receptionist.serializers import CallSessionSerializer
from receptionist.serializers import AIConfigurationSerializer
from receptionist.serializers import BusinessStatisticsSerializer


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

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a specific business."""
        business = self.get_object()

        # Get call statistics
        calls = business.calls.all()
        total_calls = calls.count()
        completed_calls = calls.filter(status='completed').count()
        failed_calls = calls.filter(status='failed').count()
        in_progress_calls = calls.filter(status='in_progress').count()

        # Calculate durations
        completed_call_durations = calls.filter(
            status='completed').values_list('duration_seconds', flat=True)
        average_duration = sum(completed_call_durations) / \
            len(completed_call_durations) if completed_call_durations else 0
        total_duration = sum(completed_call_durations)

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_calls = calls.filter(
            started_at__gte=week_ago).order_by('-started_at')[:10]

        stats_data = {
            'business': business,
            'total_calls': total_calls,
            'completed_calls': completed_calls,
            'failed_calls': failed_calls,
            'average_duration': round(average_duration, 2),
            'total_duration': total_duration,
            'recent_activity': CallSessionSerializer(recent_calls, many=True).data
        }

        serializer = BusinessStatisticsSerializer(stats_data)
        return self.response_success(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics for all businesses."""
        businesses = self.get_queryset()
        analytics_data = []

        for business in businesses:
            calls = business.calls.all()
            total_calls = calls.count()
            completed_calls = calls.filter(status='completed').count()

            # Calculate average duration
            completed_call_durations = calls.filter(
                status='completed').values_list('duration_seconds', flat=True)
            average_duration = sum(completed_call_durations) / len(
                completed_call_durations) if completed_call_durations else 0

            analytics_data.append({
                'business': business,
                'total_calls': total_calls,
                'completed_calls': completed_calls,
                'average_duration': round(average_duration, 2)
            })

        serializer = BusinessStatisticsSerializer(analytics_data, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='ai-configs')
    def ai_configs(self, request, pk=None):
        """Get health status."""
        object = self.get_object()
        ai_configurations = object.ai_configs
        serializer = AIConfigurationSerializer(ai_configurations, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='calls')
    def calls(self, request, pk=None):
        """Get all calls for a business."""
        object = self.get_object()
        business_calls = object.calls.all()
        print("Business calls:: ", business_calls)
        serializer = CallSessionSerializer(business_calls, many=True)
        return self.response_success(serializer.data)



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
