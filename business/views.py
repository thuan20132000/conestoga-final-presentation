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
    BusinessTypeSerializer, 
    BusinessListSerializer, 
    OperatingHoursSerializer, 
    ReceptionistStatisticsSerializer, 
    BusinessDashboardSerializer,
    BusinessSerializer,
    BusinessSettingsSerializer
)
from appointment.serializers import AppointmentDetailSerializer, AppointmentListSerializer
from payment.serializers import PaymentSerializer
from receptionist.serializers import CallSessionSerializer
from receptionist.serializers import AIConfigurationSerializer
from receptionist.serializers import BusinessStatisticsSerializer
from main.viewsets import BaseModelViewSet
from service.serializers import ServiceCategorySerializer, ServiceSerializer, ServiceCategoryWithServicesSerializer
from staff.serializers import StaffSerializer, StaffRoleSerializer
from client.serializers import ClientSerializer
from payment.serializers import PaymentMethodSerializer
from django.db.models import Sum, Count
from payment.models import Payment
from payment.services import PaymentService


class BusinessTypeViewSet(BaseModelViewSet):
    """ViewSet for BusinessType - read-only since these are predefined"""
    queryset = BusinessType.objects.all()
    serializer_class = BusinessTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class BusinessViewSet(BaseModelViewSet):
    """ViewSet for Business management"""
    queryset = Business.objects.all()
    # Adjust based on your authentication needs
    permission_classes = [AllowAny]
    # serializer_class = BusinessSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return BusinessListSerializer
        return BusinessSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset

    @action(detail=True, methods=['get'], url_path='operating-hours')
    def operating_hours(self, request, pk=None):
        """Get operating hours for a specific business"""
        business = self.get_object()
        hours = business.operating_hours.all()
        serializer = OperatingHoursSerializer(hours, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='business-settings')
    def business_settings(self, request, pk=None):
        """Get settings for a specific business"""
        try:
            business = self.get_object()
            settings = business.settings
            serializer = BusinessSettingsSerializer(settings)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        print("Object:: ", object)
        ai_configurations = object.ai_configs
        serializer = AIConfigurationSerializer(ai_configurations, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='calls')
    def calls(self, request, pk=None):
        """Get all calls for a business."""
        object = self.get_object()
        params = request.query_params
        from_date = params.get('started_at_from')
        to_date = params.get('started_at_to')
        if from_date and to_date:
            business_calls = object.calls.filter(
                started_at__range=(from_date, to_date)
            )
        else:
            business_calls = object.calls.all()
        serializer = CallSessionSerializer(business_calls, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='receptionist-statistics')
    def receptionist_statistics(self, request, pk=None):
        """Get receptionist statistics for a business."""
        try:
            params = request.query_params
            object = self.get_object()
            from_date = params.get('started_at_from')
            to_date = params.get('started_at_to')
            if from_date and to_date:
                business_calls = object.calls.filter(
                    started_at__range=(from_date, to_date)
                )
            else:
                business_calls = object.calls.all()
            serializer = ReceptionistStatisticsSerializer(business_calls)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        """Get dashboard data for a business."""
        try:
            object = self.get_object()
            serializer = BusinessDashboardSerializer(object)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    @action(detail=True, methods=['get'], url_path='service-categories')
    def service_categories(self, request, pk=None):
        """Get services categories for a business."""
        object = self.get_object()
        categories = object.service_categories.filter(is_active=True)
        serializer = ServiceCategorySerializer(categories, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, pk=None):
        """Get services for a business."""
        object = self.get_object()
        services = object.services.filter(is_active=True)
        serializer = ServiceSerializer(services, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='categories-services')
    def categories_services(self, request, pk=None):
        """Get services for all categories of a business."""
        object = self.get_object()
        categories = object.service_categories.filter(is_active=True)
        serializer = ServiceCategoryWithServicesSerializer(categories, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='staff')
    def staff(self, request, pk=None):
        """Get staff for a business."""
        object = self.get_object()
        staff = object.staff.all()
        serializer = StaffSerializer(staff, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='roles')
    def roles(self, request, pk=None):
        """Get roles for a business."""
        object = self.get_object()
        roles = object.staff_roles.all()
        serializer = StaffRoleSerializer(roles, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='clients')
    def clients(self, request, pk=None):
        """Get clients for a business."""
        object = self.get_object()
        clients = object.primary_clients.filter(is_active=True).order_by('-created_at')
        serializer = ClientSerializer(clients, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='appointments')
    def appointments(self, request, pk=None):   
        """Get appointments for a business."""
        object = self.get_object()
        appointments = object.appointments.all()
        serializer = AppointmentDetailSerializer(appointments, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='payment-methods')
    def payment_methods(self, request, pk=None):
        """Get payment methods for a business."""
        object = self.get_object()
        payment_methods = object.payment_methods.all()
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='payments-stats')
    def payment_stats(self, request, pk=None):
        """Get payment stats for a business."""
        try:
            object = self.get_object()
            
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            print("From date:: ", from_date)
            print("To date:: ", to_date)
            
            payment_service = PaymentService()
            payment_stats = payment_service.get_payment_stats(object, from_date, to_date)
            serializer = PaymentSerializer(payment_stats['results'], many=True)
            metadata = payment_stats['metadata']
            return self.response_success(serializer.data, metadata=metadata)
        except Exception as e:
            return self.response_error({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OperatingHoursViewSet(BaseModelViewSet):
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

    def perform_update(self, serializer):
        serializer.save(business=self.get_object().business)
        return super().perform_update(serializer)

class BusinessSettingsViewSet(BaseModelViewSet):
    """ViewSet for BusinessSettings management"""
    queryset = BusinessSettings.objects.all()
    serializer_class = BusinessSettingsSerializer
    permission_classes = [AllowAny]

    def perform_update(self, serializer):
        serializer.save(business=self.get_object().business)
        return super().perform_update(serializer)