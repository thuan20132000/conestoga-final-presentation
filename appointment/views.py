from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404

from .models import Appointment, AppointmentStatus, AppointmentReminder, AppointmentConflict, AppointmentService
from .serializers import (
    AppointmentSerializer, AppointmentListSerializer,
    AppointmentStatusSerializer, AppointmentAvailabilitySerializer,
    AppointmentReminderSerializer, AppointmentConflictSerializer, AppointmentStatsSerializer,
    AppointmentServiceSerializer
)
from client.models import Client
from client.serializers import ClientSerializer
from business.models import Business
from service.models import Service
from staff.models import Staff


class AppointmentStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointment statuses"""
    queryset = AppointmentStatus.objects.all()
    serializer_class = AppointmentStatusSerializer
    ordering = ['sort_order', 'name']


class AppointmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointments"""
    queryset = Appointment.objects.select_related(
        'client', 'service', 'staff', 'status', 'business'
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'business', 'client', 'service', 'staff', 'status', 'appointment_date',
        'is_paid', 'booking_source', 'is_recurring'
    ]
    search_fields = [
        'client__first_name', 'client__last_name', 'service__name',
        'staff__first_name', 'staff__last_name', 'notes'
    ]
    ordering_fields = [
        'appointment_date', 'start_time', 'created_at', 'total_price'
    ]
    ordering = ['appointment_date', 'start_time']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return AppointmentListSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        """Filter appointments based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__name=status_filter)
        
        # Filter by business
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(appointment_date=today)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(
            appointment_date__gte=today,
            status__name__in=['scheduled', 'confirmed']
        )
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get appointments by staff member"""
        staff_id = request.query_params.get('staff_id')
        if not staff_id:
            return Response(
                {'error': 'staff_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointments = self.get_queryset().filter(staff_id=staff_id)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get appointments by client"""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response(
                {'error': 'client_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointments = self.get_queryset().filter(client_id=client_id)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def check_availability(self, request):
        """Check appointment availability"""
        serializer = AppointmentAvailabilitySerializer(data=request.data)
        if serializer.is_valid():
            business = serializer.validated_data['business']
            service = serializer.validated_data['service']
            appointment_date = serializer.validated_data['appointment_date']
            staff = serializer.validated_data.get('staff')
            
            # Get available time slots
            available_slots = self._get_available_time_slots(
                business, service, appointment_date, staff
            )
            
            return Response({
                'available_slots': available_slots,
                'business_hours': self._get_business_hours(business, appointment_date)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        
        if appointment.status.name != 'scheduled':
            return Response(
                {'error': 'Only scheduled appointments can be confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        confirmed_status = AppointmentStatus.objects.filter(name='confirmed').first()
        if confirmed_status:
            appointment.status = confirmed_status
            appointment.confirmed_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Confirmed status not found'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        if appointment.status.name in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel completed or already cancelled appointments'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancelled_status = AppointmentStatus.objects.filter(name='cancelled').first()
        if cancelled_status:
            appointment.status = cancelled_status
            appointment.cancelled_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Cancelled status not found'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark appointment as completed"""
        appointment = self.get_object()
        
        if appointment.status.name in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot complete already completed or cancelled appointments'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        completed_status = AppointmentStatus.objects.filter(name='completed').first()
        if completed_status:
            appointment.status = completed_status
            appointment.completed_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Completed status not found'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get appointment statistics"""
        business_id = request.query_params.get('business')
        queryset = self.get_queryset()
        
        if business_id:
            queryset = queryset.filter(business_id=business_id)
        
        # Calculate statistics
        total_appointments = queryset.count()
        completed_appointments = queryset.filter(status__name='completed').count()
        cancelled_appointments = queryset.filter(status__name='cancelled').count()
        upcoming_appointments = queryset.filter(
            appointment_date__gte=timezone.now().date(),
            status__name__in=['scheduled', 'confirmed']
        ).count()
        today_appointments = queryset.filter(appointment_date=timezone.now().date()).count()
        
        # Revenue calculations
        today_revenue = queryset.filter(
            appointment_date=timezone.now().date(),
            status__name='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        this_month_start = timezone.now().date().replace(day=1)
        this_month_revenue = queryset.filter(
            appointment_date__gte=this_month_start,
            status__name='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        avg_appointment_value = queryset.filter(
            status__name='completed'
        ).aggregate(avg=Avg('total_price'))['avg'] or 0
        
        # No-show rate calculation
        no_show_count = queryset.filter(status__name='no_show').count()
        no_show_rate = (no_show_count / total_appointments * 100) if total_appointments > 0 else 0
        
        stats_data = {
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'upcoming_appointments': upcoming_appointments,
            'today_appointments': today_appointments,
            'revenue_today': today_revenue,
            'revenue_this_month': this_month_revenue,
            'average_appointment_value': avg_appointment_value,
            'no_show_rate': no_show_rate
        }
        
        serializer = AppointmentStatsSerializer(stats_data)
        return Response(serializer.data)
    
    def _get_available_time_slots(self, business, service, appointment_date, staff=None):
        """Get available time slots for a given date"""
        # Get business operating hours for the day
        day_of_week = appointment_date.weekday()
        operating_hours = business.operating_hours.filter(day_of_week=day_of_week).first()
        
        if not operating_hours or not operating_hours.is_open:
            return []
        
        # Get time slot interval from business settings
        time_interval = business.settings.time_slot_interval if hasattr(business, 'settings') else 15
        
        # Calculate available time slots
        available_slots = []
        current_time = operating_hours.open_time
        
        while current_time < operating_hours.close_time:
            end_time = (datetime.combine(date.today(), current_time) + 
                       timedelta(minutes=service.duration_minutes)).time()
            
            if end_time <= operating_hours.close_time:
                # Check if staff is available for this time slot
                if staff:
                    conflicting_appointments = Appointment.objects.filter(
                        staff=staff,
                        appointment_date=appointment_date,
                        status__name__in=['scheduled', 'confirmed']
                    ).exclude(
                        Q(end_time__lte=current_time) | Q(start_time__gte=end_time)
                    )
                    
                    if not conflicting_appointments.exists():
                        available_slots.append({
                            'start_time': current_time.strftime('%H:%M'),
                            'end_time': end_time.strftime('%H:%M'),
                            'staff_id': staff.id,
                            'staff_name': staff.get_full_name()
                        })
                else:
                    # If no specific staff requested, find available staff
                    available_staff = self._get_available_staff_for_timeslot(
                        business, appointment_date, current_time, end_time, service
                    )
                    
                    for staff_member in available_staff:
                        available_slots.append({
                            'start_time': current_time.strftime('%H:%M'),
                            'end_time': end_time.strftime('%H:%M'),
                            'staff_id': staff_member.id,
                            'staff_name': staff_member.get_full_name()
                        })
            
            # Move to next time slot
            current_time = (datetime.combine(date.today(), current_time) + 
                           timedelta(minutes=time_interval)).time()
        
        return available_slots
    
    def _get_available_staff_for_timeslot(self, business, appointment_date, start_time, end_time, service):
        """Get staff members available for a specific time slot"""
        # Get staff members who can provide this service
        available_staff = Staff.objects.filter(
            business=business,
            staff_services__service=service,
            staff_services__is_active=True,
            is_active=True
        ).distinct()
        
        # Filter out staff with conflicting appointments
        available_staff = available_staff.exclude(
            appointments__appointment_date=appointment_date,
            appointments__status__name__in=['scheduled', 'confirmed']
        ).exclude(
            appointments__start_time__lt=end_time,
            appointments__end_time__gt=start_time
        )
        
        return available_staff
    
    def _get_business_hours(self, business, appointment_date):
        """Get business hours for a specific date"""
        day_of_week = appointment_date.weekday()
        operating_hours = business.operating_hours.filter(day_of_week=day_of_week).first()
        
        if operating_hours and operating_hours.is_open:
            return {
                'is_open': True,
                'open_time': operating_hours.open_time.strftime('%H:%M'),
                'close_time': operating_hours.close_time.strftime('%H:%M')
            }
        
        return {'is_open': False}


class AppointmentReminderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointment reminders"""
    queryset = AppointmentReminder.objects.all()
    serializer_class = AppointmentReminderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment', 'reminder_type', 'is_sent', 'is_delivered']


class AppointmentServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointment services"""
    queryset = AppointmentService.objects.all()
    serializer_class = AppointmentServiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['appointment', 'service', 'staff', 'is_requested', 'is_active']
    search_fields = ['service__name', 'staff__first_name', 'staff__last_name']
    ordering_fields = ['created_at', 'custom_price', 'custom_duration']
    ordering = ['appointment', 'service__name']


class AppointmentConflictViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointment conflicts"""
    queryset = AppointmentConflict.objects.all()
    serializer_class = AppointmentConflictSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['appointment', 'conflict_type', 'is_resolved']
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a conflict"""
        conflict = self.get_object()
        conflict.is_resolved = True
        conflict.resolved_at = timezone.now()
        conflict.resolved_by = request.user if hasattr(request, 'user') else None
        conflict.save()
        
        serializer = self.get_serializer(conflict)
        return Response(serializer.data)