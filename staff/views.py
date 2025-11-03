from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Staff, StaffService, StaffWorkingHours, StaffOffDay
from .serializers import (
    StaffSerializer,
    StaffCreateUpdateSerializer,
    StaffServiceSerializer,
    StaffRoleSerializer,
    StaffWorkingHoursSerializer,
    StaffWorkingHoursCreateUpdateSerializer,
    StaffOffDaySerializer,
    StaffOffDayCreateUpdateSerializer,
)
from business.models import Business
from main.viewsets import BaseModelViewSet


class StaffViewSet(BaseModelViewSet):
    """ViewSet for Staff management"""
    queryset = Staff.objects.select_related('business')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business', 'role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'bio']
    ordering_fields = ['last_name', 'first_name', 'hire_date', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffCreateUpdateSerializer
        return StaffSerializer
    
    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """Get staff roles"""
        staff = self.get_object()
        roles = staff.roles.all()
        serializer = StaffRoleSerializer(roles, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='working-hours')
    def working_hours(self, request, pk=None):
        """Get staff working hours"""
        staff = self.get_object()
        print("staff", staff)
        working_hours = staff.working_hours.all()
        print("working_hours", working_hours)
        serializer = StaffWorkingHoursSerializer(working_hours, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='off-days')
    def off_days(self, request, pk=None):
        """Get staff off days"""
        staff = self.get_object()
        off_days = staff.staff_off_days.all()
        serializer = StaffOffDaySerializer(off_days, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get', 'post', 'delete'])
    def services(self, request, pk=None):
        """Manage staff services"""
        staff = self.get_object()
        
        if request.method == 'GET':
            staff_services = staff.staff_services.all()
            serializer = StaffServiceSerializer(staff_services, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            service_id = request.data.get('service_id')
            is_primary = request.data.get('is_primary', False)
            
            if not service_id:
                return Response(
                    {'error': 'service_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate that the service exists and belongs to the same business
            try:
                from service.models import Service
                service = Service.objects.get(id=service_id, business=staff.business)
            except:
                return Response(
                    {'error': 'Service not found or does not belong to this business'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            staff_service, created = StaffService.objects.get_or_create(
                staff=staff, service_id=service_id, defaults={'is_primary': is_primary}
            )
            
            if not created:
                staff_service.is_primary = is_primary
                staff_service.save()
            
            serializer = StaffServiceSerializer(staff_service)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            service_id = request.data.get('service_id')
            if not service_id:
                return Response(
                    {'error': 'service_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                staff_service = StaffService.objects.get(staff=staff, service_id=service_id)
                staff_service.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except StaffService.DoesNotExist:
                return Response(
                    {'error': 'Staff service not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
class StaffWorkingHoursViewSet(BaseModelViewSet):
    """ViewSet for Staff working hours"""
    queryset = StaffWorkingHours.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffWorkingHoursCreateUpdateSerializer
        return StaffWorkingHoursSerializer
    
class StaffOffDayViewSet(BaseModelViewSet):
    """ViewSet for Staff off days"""
    queryset = StaffOffDay.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffOffDayCreateUpdateSerializer
        return StaffOffDaySerializer