from rest_framework import status
from rest_framework.decorators import APIView, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from django_filters import rest_framework as filters
from django.db import transaction

from payment.models import Payment, PaymentStatusType
from business.models import Business
from service.models import ServiceCategory
from .models import Appointment, AppointmentService
from client.models import Client
from client.serializers import ClientSerializer, BookingClientSerializer, BookingClientCreateSerializer

from .serializers import (
    AppointmentSerializer,
    AppointmentAvailabilitySerializer,
    AppointmentStatsSerializer,
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentUpdateSerializer,
    AppointmentServiceSerializer,
    AppointmentHistorySerializer
)
from main.viewsets import BaseModelViewSet, BaseViewSet
from staff.serializers import StaffCalendarSerializer
from staff.models import Staff, StaffOffDay
from payment.serializers import PaymentSerializer, PaymentDetailSerializer
from service.serializers import BusinessBookingServiceCategorySerializer
from staff.serializers import BusinessBookingStaffSerializer
from .services import BusinessBookingService
from business.serializers import BusinessSerializer, BusinessInfoSerializer
from appointment.services import BusinessStaffService
from appointment.models import AppointmentStatusType
from staff.permissions import IsBusinessManager
from appointment.services import TicketReportService
from appointment.serializers import BusinessTicketReportSerializer, StaffTicketReportSerializer

class AppointmentFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='business_id')
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
    filterset_class = AppointmentFilter
    ordering = ['-updated_at']
    permission_classes = [IsAuthenticated]
    
    
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
    
    # get only appointments for a specific staff
    def get_staff_appointments(self, user):
        """Get staff appointments"""
        queryset = self.get_filtered_queryset().filter(appointment_services__staff_id=user.id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List appointments"""
        appointments = self.get_filtered_queryset()
        self.paginator.page_size = request.query_params.get('page_size', 100)
        
        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = AppointmentDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
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
            with transaction.atomic():
                instance = self.get_object()
                instance.is_active = False
                instance.payments.all().update(status=PaymentStatusType.FAILED)
                instance.save()
                return self.response_success(AppointmentSerializer(instance).data)
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get history of an appointment"""
        try:
            instance = self.get_object()
            history = instance.history.all().order_by('-history_date')
            print("history", history)
            return self.response_success(AppointmentHistorySerializer(history, many=True).data)
        except Exception as e:
            return self.response_error(str(e))
    
    # create appointment with appointment services
    @action(detail=False, methods=['post'], url_path='appointment-services')
    def create_appointment_services(self, request):
        """Create appointment with appointment services"""
        try:
            with transaction.atomic():
                appointment_services = request.data['appointment_services']
                appointment = Appointment.objects.create(
                    business_id=request.data['business_id'],
                    client_id=request.data['client'],
                    appointment_date=request.data['appointment_date'],
                    notes=request.data['notes'],
                    internal_notes=request.data['internal_notes'],
                    booking_source=request.data['booking_source'],
                    start_at=request.data['start_at'],
                    end_at=request.data['end_at'],
                    metadata=request.data['metadata'],
                    
                )
                for appointment_service in appointment_services:
                    AppointmentService.objects.create(
                        id=appointment_service['id'],
                        appointment=appointment,
                        service_id=appointment_service['service'],
                        staff_id=appointment_service['staff'],
                        is_staff_request=appointment_service['is_staff_request'],
                        start_at=appointment_service['start_at'],
                        end_at=appointment_service['end_at'],
                        custom_price=appointment_service['custom_price'] or appointment_service['service'].price,
                    )
                
                return self.response_success(AppointmentDetailSerializer(appointment).data)
        except Exception as e:
            print("error", e)
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
                appointment.appointment_date = request.data.get('appointment_date', appointment.appointment_date)
                appointment.start_at = request.data.get('start_at', appointment.start_at)
                appointment.end_at = request.data.get('end_at', appointment.end_at)
                appointment.metadata = request.data.get('metadata', appointment.metadata)
                appointment.save()
                
                # update appointment services
                appointment_services = request.data['appointment_services']
                for appointment_service in appointment_services:
                    service_id = appointment_service['service']
                    staff_id = appointment_service['staff']
                    is_staff_request = appointment_service['is_staff_request']
                    start_at = appointment_service['start_at']
                    end_at = appointment_service['end_at']
                    custom_price = appointment_service.get('custom_price', None)
                    custom_duration = appointment_service.get('custom_duration', None)
                    metadata = appointment_service.get('metadata', None)
                    
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
                        appointment_service_obj.custom_price = custom_price
                        appointment_service_obj.custom_duration = custom_duration
                        appointment_service_obj.metadata = metadata
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
                            custom_price=custom_price,
                            custom_duration=custom_duration,
                            metadata=metadata,
                        )
                return self.response_success(AppointmentDetailSerializer(appointment).data)
        except Exception as e:
            print("error", e)
            return self.response_error(str(e), status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='calendar-staffs')
    def calendar_staffs(self, request):
        """Get calendar staffs"""
        try:
            business_id = request.query_params.get('business_id')
            appointment_date = request.query_params.get('appointment_date')
            auth_user = request.user
            
            if not business_id or not appointment_date:
                return self.response_error(
                    {'error': 'business_id and appointment_date parameters are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            weekday = datetime.strptime(appointment_date, '%Y-%m-%d').weekday()
            
            # Get staff with role and who are working on the appointment date
            if auth_user.role.name in ['Manager', 'Owner']:
                business_staffs = Staff.objects.filter(
                    business_id=business_id,
                    is_active=True,
                    is_online_booking_allowed=True,
                    working_hours__is_working=True,
                    working_hours__day_of_week=weekday,
                    role__name__in=['Technician', 'Stylist'],
                )
            else:
                business_staffs = Staff.objects.filter(
                    id=auth_user.id,
                )
            
            
            # Get staff who have an off day on the appointment date
            staff_off_days = StaffOffDay.objects.filter(
                staff__id__in=business_staffs.values_list('id', flat=True),
                start_date__lte=appointment_date,
                end_date__gte=appointment_date,
            )
            
            
            # Get staff who are available for the appointment date
            if staff_off_days.exists():
                staff_on_leave_ids = staff_off_days.values_list('staff__id', flat=True)
                staff_off_day_appointments = AppointmentService.objects.filter(
                    staff_id__in=staff_on_leave_ids,
                    appointment__appointment_date=appointment_date,
                )
                staff_on_leave_with_appointments = staff_off_day_appointments.values_list('staff_id', flat=True)
                
                staff_on_leave_without_appointments = staff_on_leave_ids.exclude(id__in=list(staff_on_leave_with_appointments))
                
                available_staffs = business_staffs.exclude(id__in=staff_on_leave_without_appointments)
            else:
                available_staffs = business_staffs
                
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
            user = request.user
            appointments = self.get_filtered_queryset()
            if user.role.name in ['Technician', 'Stylist']:
                appointments = self.get_staff_appointments(user)
            appointments_statistics = self._get_appointments_statistics(appointments)
            appointments_data = AppointmentDetailSerializer(appointments, many=True).data
            return self.response_success(appointments_data, metadata=appointments_statistics)
        
        except Exception as e:
            return self.response_error(str(e))
    
    # payments
    @action(detail=True, methods=['get'], url_path='payments')
    def payments(self, request, pk=None):
        """Get payments for an appointment"""
        try:
            appointment = self.get_object()
            payments = Payment.objects.filter(appointment=appointment)
            serializer = PaymentDetailSerializer(payments, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=True, methods=['get'], url_path='latest-payment')
    def latest_payment(self, request, pk=None):
        """Get latest payment for an appointment"""
        try:
            appointment = self.get_object()
            if not appointment:
                return self.response_error(
                    {'error': 'Appointment not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            latest_payment = Payment.objects.filter(appointment=appointment).order_by('-created_at').first()
            serializer = PaymentDetailSerializer(latest_payment)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
        
    
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
            print("request.data", request.data)
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
            
# Booking appointments viewset for client's booking pages
class BusinessBookingViewSet(BaseModelViewSet):
    """ViewSet for managing booking pages"""
    
    
    http_method_names = ['get', 'post']
    
    @action(detail=False, methods=['get'], url_path='business-info')
    def business_info(self, request):
        """Get business info"""
        try:
            business_id = request.query_params.get('business_id')
            if not business_id:
                return self.response_error(
                    {'error': 'business_id parameter is required'}, 
                    status_code=status.HTTP_400_BAD_REQUEST)
            business = Business.objects.filter(is_deleted=False, id=business_id).first()
            if not business:
                return self.response_error(
                    {'error': 'Business not found'}, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            serializer = BusinessInfoSerializer(business)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to retrieve business info")
    
    @action(
        detail=False, 
        methods=['get'], 
        url_path='business', 
        permission_classes=[AllowAny]
    )
    def business(self, request):
        """Get business"""
        try:
            
            business_id = request.query_params.get('business_id')
            if not business_id:
                return self.response_error(
                    {'error': 'business_id parameter is required'}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            business = Business.objects.filter(is_deleted=False, id=business_id).first()
            if not business:
                return self.response_error(
                    {'error': 'Business not found'}, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            serializer = BusinessSerializer(business)
            return self.response_success(serializer.data, message="Business retrieved successfully")
        except Exception as e:
            return self.response_error(str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to retrieve business")

    
    @action(
        detail=False, 
        methods=['get'], 
        url_path='categories-services', 
        permission_classes=[AllowAny]
    )
    def categories_services(self, request):
        """Get business services"""
        business_id = request.query_params.get('business_id')
        if not business_id:
            return self.response_error(
                {'error': 'business_id parameter is required'}, 
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        categories_services = ServiceCategory.objects.filter(business_id=business_id)
        serializer = BusinessBookingServiceCategorySerializer(categories_services, many=True)
        return self.response_success(serializer.data)
    
    # available staffs for specific service and date
    @action(detail=False, methods=['get'], url_path='technicians')
    def technicians(self, request):
        """Get technicians for a specific service and date"""
        try:
            print("request.query_params", request.query_params)
            business_id = request.query_params.get('business_id')
            if not business_id:
                return self.response_error(
                    {'error': 'business_id parameter is required'}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            business_staff = BusinessStaffService(business_id)
            technicians = business_staff.get_business_active_technicians()
            return self.response_success(BusinessBookingStaffSerializer(technicians, many=True).data)
        
        except Exception as e:
            return self.response_error(str(e))
        
    @action(detail=False, methods=['get'], url_path='available-time-slots')
    def available_time_slots(self, request):
        """Get available time slots for a specific service and date"""
        try:
            business_id = request.query_params.get('business_id')
            service_ids = request.query_params.getlist('service_ids[]')
            duration = request.query_params.get('duration')
            date = request.query_params.get('date')
            staff_id = request.query_params.get('staff_id')
            interval_minutes = request.query_params.get('interval_minutes',15)
            
            booking_service = BusinessBookingService(
                business_id=business_id,
                interval_minutes=int(interval_minutes)
            )
            
            if staff_id:
                available_time_slots_for_staff = booking_service.get_staff_time_slots(
                    staff_id=staff_id,
                    service_ids=service_ids,
                    appointment_date=date,
                    service_duration=duration
                )
                return self.response_success(available_time_slots_for_staff)
            else:
                available_time_slots = booking_service.get_all_available_time_slots(
                    business_id=business_id,
                    service_ids=service_ids,
                    appointment_date=date,
                    service_duration=duration
                )
                return self.response_success(available_time_slots)
        except Exception as e:
            return self.response_error(str(e))
        
    
    @action(detail=False, methods=['get'], url_path='client-by-phone')
    def client_by_phone(self, request):
        """Get client for a specific business"""
        try:
            business_id = request.query_params.get('business_id')
            phone = request.query_params.get('phone')
            if not business_id or not phone:
                return self.response_error(
                    {'error': 'business_id and phone parameters are required'}, 
                    status_code=status.HTTP_400_BAD_REQUEST)
            
            client = Client.objects.filter(
                primary_business_id=business_id, 
                phone=phone,
                is_active=True,
                is_deleted=False
            ).first()
            
            print("client", client)
            
            if not client:
                return self.response_error(
                    {'error': 'Client not found'}, 
                    status_code=status.HTTP_404_NOT_FOUND)
            return self.response_success(BookingClientSerializer(client).data)
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=False, methods=['post'], url_path='client')
    def client(self, request):
        """Create a client for a specific business"""
        try:
            print("request.data", request.data)
            serializer = BookingClientCreateSerializer(data=request.data)
            print("serializer", serializer)
            serializer.is_valid(raise_exception=True)
            client = serializer.update_or_create(serializer.validated_data)
            print("client", client)
            
            return self.response_success(client, message="Client created successfully")
        except Exception as e:
            return self.response_error(str(e))
        

    @action(detail=False, methods=['post'], url_path='appointment')
    def create_appointment(self, request):
        """Make an appointment"""
        print("create appointment request.data", request.data)
        try:
            
            appointment_data = request.data
            appointment_services = appointment_data.pop('appointment_services', [])
            print("appointment_data", appointment_data)
            print("appointment_services", appointment_services)
            
            appointment_service = BusinessBookingService(
                business_id=appointment_data.get('business_id'),
                interval_minutes=appointment_data.get('interval_minutes', 0)
            )
            created_appointment = appointment_service.create_appointment_services(
                appointment=appointment_data,
                appointment_services=appointment_services
            )
            appointment_serializer = AppointmentDetailSerializer(created_appointment)
            return self.response_success(appointment_serializer.data)
        except Exception as e:
            print("error", e)
            return self.response_error(str(e))
        

class  POSAppointmentFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='business_id', required=True)
    appointment_date = filters.DateFilter(field_name='appointment_date', required=True)
    status = filters.CharFilter(field_name='status')
    booked_by = filters.NumberFilter(field_name='booked_by')
    booking_source = filters.CharFilter(field_name='booking_source')
    class Meta:
        model = Appointment
        fields = ['business_id', 'appointment_date', 'status', 'booked_by', 'booking_source']
        
class POSAppointmentViewSet(BaseModelViewSet):
    """ViewSet for managing POS appointments"""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentDetailSerializer
    filterset_class = POSAppointmentFilter
    
    def get_queryset(self):
        """Get queryset for POS appointments"""
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True, is_deleted=False)
        return queryset
    
    def list(self, request):
        """List POS appointments"""
        try:
            queryset = self.get_queryset()
            appointments = self.filter_queryset(queryset)
            serializer = AppointmentDetailSerializer(appointments, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(
                str(e), 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                message="Failed to retrieve POS appointments"
            )
            
class SalesReportFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='business_id', required=True)
    appointment_date = filters.DateFilter(field_name='appointment_date', required=True)
    status = filters.CharFilter(field_name='status')
    booked_by = filters.NumberFilter(field_name='booked_by')
    booking_source = filters.CharFilter(field_name='booking_source')
    class Meta:
        model = AppointmentService
        fields = ['business_id', 'appointment_date', 'status', 'booked_by', 'booking_source']
class SalesReportViewSet(BaseModelViewSet):
    """ViewSet for managing sales reports"""
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    filterset_class = SalesReportFilter
    queryset = AppointmentService.objects.all()
    
    def get_queryset(self):
        """Get queryset for sales reports"""
        queryset = super().get_queryset()
        queryset = queryset.filter(appointment__business_id=self.request.user.business_id)
        return queryset
    
    def list(self, request):
        """List sales reports"""
        try:
            queryset = self.get_queryset()
            sales_report = self.filter_queryset(queryset)
            serializer = AppointmentServiceSerializer(sales_report, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
        
class TicketReportFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='business_id', required=True)
    appointment_date = filters.DateFilter(field_name='appointment_date', required=True)
    status = filters.CharFilter(field_name='status')
    booked_by = filters.NumberFilter(field_name='booked_by')
    booking_source = filters.CharFilter(field_name='booking_source')
    class Meta:
        model = AppointmentService
        fields = ['business_id', 'appointment_date', 'status', 'booked_by', 'booking_source']
        
class TicketReportViewSet(BaseModelViewSet):
    """ViewSet for managing ticket reports"""
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    filterset_class = TicketReportFilter
    queryset = AppointmentService.objects.all()
    
    def get_queryset(self):
        """Get queryset for ticket reports"""
        queryset = super().get_queryset()
        queryset = queryset.filter(appointment__business_id=self.request.user.business_id)
        return queryset
    
    
    def list(self, request):
        """List ticket reports"""
        try:
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            staff_id = request.query_params.get('staff_id')
            
            user = self.request.user
            if not IsBusinessManager().has_permission(self.request, self):
                staff_id = user.id
            
            ticket_report = TicketReportService(self.request.user.business_id)
            ticket_report_data = ticket_report.get_ticket_report_summary(from_date, to_date, staff_id)
            
            print("ticket_report_data", ticket_report_data)
            serializer = BusinessTicketReportSerializer(ticket_report_data)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
        
    @action(detail=False, methods=['get'], url_path='by-dates', permission_classes=[IsAuthenticated])
    def ticket_report_by_dates(self, request):
        """Get ticket report by dates"""
        try:    
            staff_id = request.query_params.get('staff_id')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            ticket_report = TicketReportService(self.request.user.business_id)
            ticket_report_data = ticket_report.get_ticket_report_by_dates(from_date, to_date, staff_id)
            serializer = BusinessTicketReportSerializer(ticket_report_data)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
        
    @action(detail=False, methods=['get'], url_path='by-date', permission_classes=[IsAuthenticated])
    def ticket_report_by_date(self, request):
        """Get ticket report by staff"""
        try:
            staff_id = request.query_params.get('staff_id')
            date = request.query_params.get('date')
            
            if not staff_id or not date:
                return self.response_error(
                    {'error': 'staff_id and date parameters are required'}, 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
            ticket_report = TicketReportService(self.request.user.business_id)
            ticket_report_data = ticket_report.get_ticket_report_by_date(staff_id, date)
            serializer = StaffTicketReportSerializer(ticket_report_data)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))