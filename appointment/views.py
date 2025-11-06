from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from django.db import transaction
from .models import Appointment, AppointmentService

from .serializers import (
    AppointmentSerializer,
    AppointmentAvailabilitySerializer,
    AppointmentStatsSerializer,
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentUpdateSerializer,
    AppointmentListSerializer,
    AppointmentServiceSerializer
)
from main.viewsets import BaseModelViewSet
from staff.serializers import StaffCalendarSerializer
from staff.models import Staff
from service.models import Service
from service.serializers import ServiceSerializer

import json
class AppointmentFilter(filters.FilterSet):
    business_id = filters.NumberFilter(field_name='business_id')
    appointment_date = filters.DateFilter(field_name='appointment_date')
    status = filters.CharFilter(field_name='status')
    booked_by = filters.NumberFilter(field_name='booked_by')
    booking_source = filters.CharFilter(field_name='booking_source')
    class Meta:
        model = Appointment
        fields = ['business_id', 'appointment_date', 'status', 'booked_by', 'booking_source']

class AppointmentViewSet(BaseModelViewSet):
    """ViewSet for managing appointments"""
    queryset = Appointment.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppointmentFilter
    ordering_fields = ['appointment_date', 'created_at']
    ordering = ['-appointment_date', '-created_at']
    search_fields = [
        'client__first_name', 
        'client__last_name', 
        'client__email', 
        'client__phone', 
        'booked_by__first_name', 
        'booked_by__last_name', 
        'booked_by__email', 
        'booked_by__phone',
        'business__name'
    ]
    
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        if self.action == 'create':
            return AppointmentCreateSerializer
        if self.action == 'retrieve':
            return AppointmentDetailSerializer
        return AppointmentSerializer

    def get_queryset(self):
        """Get queryset for appointments"""
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset
    
    def get_filtered_queryset(self):
        """Get queryset for appointments"""
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List appointments"""
        appointments = self.get_queryset()
        appointments = self.filter_queryset(appointments)
        serializer = AppointmentDetailSerializer(appointments, many=True)
        return self.response_success(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve an appointment"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.response_success(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update an appointment"""
        try:
            instance = self.get_object()   
            serializer = AppointmentUpdateSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_appointment = serializer.update(instance, serializer.validated_data)
            return self.response_success(updated_appointment)
        except Exception as e:
            return self.response_error(str(e))
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            created_appointment = serializer.create(serializer.validated_data)
            return self.response_success(created_appointment)
        except Exception as e:
            return self.response_error(str(e))
    
    def destroy(self, request, *args, **kwargs):
        """Destroy an appointment"""
        try:
            instance = self.get_object()
            instance.is_active = False
            instance.save()
            print("instance", instance)
            print("AppointmentSerializer(instance).data", AppointmentSerializer(instance).data)
            return self.response_success(AppointmentSerializer(instance).data)
        except Exception as e:
            return self.response_error(str(e))
    
    # create appointment with appointment services
    @action(detail=False, methods=['post'], url_path='appointment-services')
    def create_appointment_services(self, request):
        """Create appointment with appointment services"""
        try:
            with transaction.atomic():
                appointment = Appointment.objects.create(
                    business_id=request.data['business'],
                    client_id=request.data['client'],
                    appointment_date=request.data['appointment_date'],
                    notes=request.data['notes'],
                    internal_notes=request.data['internal_notes'],
                    booking_source=request.data['booking_source'],
                )
                appointment_services = request.data['appointment_services']
                print("appointment_services", appointment_services)
                for appointment_service in appointment_services:
                    AppointmentService.objects.create(
                        id=appointment_service['id'],
                        appointment=appointment,
                        service_id=appointment_service['service'],
                        staff_id=appointment_service['staff'],
                        is_staff_request=appointment_service['is_staff_request'],
                        start_at=appointment_service['start_at'],
                        end_at=appointment_service['end_at'],
                    )
                return self.response_success(AppointmentDetailSerializer(appointment).data)
        except Exception as e:
            return self.response_error(str(e))
    
    # update appointment with appointment services
    @action(detail=True, methods=['PATCH'], url_path='appointment-services')
    def update_appointment_services(self, request, pk=None):
        """Update appointment with appointment services"""
        try:
            with transaction.atomic():
                appointment = self.get_object()
                
                # update appointment
                appointment.client_id = request.data.get('client', appointment.client)
                appointment.notes = request.data.get('notes', appointment.notes)
                appointment.internal_notes = request.data.get('internal_notes', appointment.internal_notes)
                appointment.status = request.data.get('status', appointment.status)
                appointment.save()
                
                # update appointment services
                appointment_services = request.data['appointment_services']
                for appointment_service in appointment_services:
                    service_id = appointment_service['service']
                    staff_id = appointment_service['staff']
                    is_staff_request = appointment_service['is_staff_request']
                    start_at = appointment_service['start_at']
                    end_at = appointment_service['end_at']
                    id = appointment_service['id']
                    try:
                        appointment_service_obj = AppointmentService.objects.get(id=id)
                    except AppointmentService.DoesNotExist:
                        appointment_service_obj = None
                    if appointment_service_obj:
                        appointment_service_obj.staff_id = staff_id
                        appointment_service_obj.start_at = start_at
                        appointment_service_obj.end_at = end_at
                        appointment_service_obj.service_id = service_id
                        appointment_service_obj.is_staff_request = is_staff_request
                        appointment_service_obj.save()
                    else:
                        AppointmentService.objects.create(
                            id=id,
                            appointment=appointment,
                            service_id=service_id,
                            staff_id=staff_id,
                            is_staff_request=is_staff_request,
                            start_at=start_at,
                            end_at=end_at,
                        )
                return self.response_success(AppointmentDetailSerializer(appointment).data)
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=False, methods=['get'], url_path='calendar-staffs')
    def calendar_staffs(self, request):
        """Get calendar staffs"""
        try:
            business_id = request.query_params.get('business_id')
            appointment_date = request.query_params.get('appointment_date')
            if not business_id or not appointment_date:
                return self.response_error(
                    {'error': 'business_id and appointment_date parameters are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            weekday = datetime.strptime(appointment_date, '%Y-%m-%d').weekday()
            
            # Get staff who are working on the appointment date
            business_staffs = Staff.objects.filter(
                business_id=business_id,
                is_active=True,
                is_online_booking_allowed=True,
                working_hours__is_working=True,
                working_hours__day_of_week=weekday,
            )
            
            # Get staff who have an off day on the appointment date
            business_day_off_staffs = business_staffs.filter(
                staff_off_days__start_date__lte=appointment_date,
                staff_off_days__end_date__gte=appointment_date,
            )
            
            # Get staff who are available for the appointment date
            available_staffs = business_staffs.exclude(id__in=business_day_off_staffs.values_list('id', flat=True))
            serializer = StaffCalendarSerializer(
                available_staffs, 
                many=True, 
                context={
                    'appointment_date': appointment_date, 
                    'weekday': weekday,
                }
            )
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
    
    def _get_appointments_statistics(self, appointments_queryset) -> dict:
        """Get appointments statistics"""
        total_appointments = appointments_queryset.count()
        total_completed_appointments = appointments_queryset.filter(status='completed').count()
        total_cancelled_appointments = appointments_queryset.filter(status='cancelled').count()

        statistics_data = {
            'total_appointments': total_appointments,
            'total_completed_appointments': total_completed_appointments,
            'total_cancelled_appointments': total_cancelled_appointments,
            
        }
        return statistics_data
    
    @action(detail=False, methods=['get'], url_path='calendar-appointments')
    def calendar_appointments(self, request):
        """Get today's appointments"""
        try:
            all_appointments = self.get_filtered_queryset()
            appointments_statistics = self._get_appointments_statistics(all_appointments)
            appointments_data = AppointmentDetailSerializer(all_appointments, many=True).data
            return self.response_success(appointments_data, metadata=appointments_statistics)
        
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        today = timezone.now().date()
        appointments = self.get_queryset().filter(
            appointment_date__gte=today,
            status__name__in=['scheduled', 'confirmed']
        )
        serializer = self.get_serializer(appointments, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get appointments by staff member"""
        staff_id = request.query_params.get('staff_id')
        if not staff_id:
            return self.response_error(
                {'error': 'staff_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointments = self.get_queryset().filter(staff_id=staff_id)
        serializer = self.get_serializer(appointments, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get appointments by client"""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return self.response_error(
                {'error': 'client_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointments = self.get_queryset().filter(client_id=client_id)
        serializer = self.get_serializer(appointments, many=True)
        return self.response_success(serializer.data)
    
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
            
            return self.response_success({
                'available_slots': available_slots,
                'business_hours': self._get_business_hours(business, appointment_date)
            })
        
        return self.response_error(serializer.errors)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        
        if appointment.status.name != 'scheduled':
            return self.response_error(
                {'error': 'Only scheduled appointments can be confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        confirmed_status = AppointmentStatus.objects.filter(name='confirmed').first()
        if confirmed_status:
            appointment.status = confirmed_status
            appointment.confirmed_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return self.response_success(serializer.data)
        
        return self.response_error(
            {'error': 'Confirmed status not found'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        if appointment.status.name in ['completed', 'cancelled']:
            return self.response_error(
                {'error': 'Cannot cancel completed or already cancelled appointments'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cancelled_status = AppointmentStatus.objects.filter(name='cancelled').first()
        if cancelled_status:
            appointment.status = cancelled_status
            appointment.cancelled_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return self.response_success(serializer.data)
        
        return self.response_error(
            {'error': 'Cancelled status not found'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark appointment as completed"""
        appointment = self.get_object()
        
        if appointment.status.name in ['completed', 'cancelled']:
            return self.response_error(
                {'error': 'Cannot complete already completed or cancelled appointments'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        completed_status = AppointmentStatus.objects.filter(name='completed').first()
        if completed_status:
            appointment.status = completed_status
            appointment.completed_at = timezone.now()
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return self.response_success(serializer.data)
        
        return self.response_error(
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
        return self.response_success(serializer.data)
    
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


class AppointmentServiceViewSet(BaseModelViewSet):
    """ViewSet for managing appointment services"""
    queryset = AppointmentService.objects.all()
    serializer_class = AppointmentServiceSerializer
    
    def list(self, request, *args, **kwargs):
        """List appointment services"""
        appointment_id = request.query_params.get('appointment_id')
        if not appointment_id:
            return self.response_error(
                {'error': 'appointment_id parameter is required'}, 
                status_code=status.HTTP_400_BAD_REQUEST
            )
        appointment_services = self.get_queryset().filter(appointment_id=appointment_id)
        serializer = self.get_serializer(appointment_services, many=True)
        return self.response_success(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve an appointment service"""
        appointment_service = self.get_object()
        serializer = self.get_serializer(appointment_service)
        return self.response_success(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create an appointment service"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            created_appointment_service = serializer.create(serializer.validated_data)
            return self.response_success(AppointmentServiceSerializer(created_appointment_service).data)
        except Exception as e:
            return self.response_error(str(e))
        
    def partial_update(self, request, *args, **kwargs):
        """Partial update an appointment service"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
    
    def destroy(self, request, *args, **kwargs):
        """Destroy an appointment service"""
        try:
            instance = self.get_object()
            instance.delete()
            return self.response_success(
                data=None,
                message="Appointment service deleted successfully"
            )
        except Exception as e:
            return self.response_error(
                data=str(e),
                message="Failed to delete appointment service"
            )
    
