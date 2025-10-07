from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Staff, StaffService
from .serializers import (
    StaffSerializer, StaffCreateUpdateSerializer, StaffServiceSerializer
)
from business.models import Business


class StaffViewSet(viewsets.ModelViewSet):
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