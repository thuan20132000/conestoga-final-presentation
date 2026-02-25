from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Client
from .serializers import (
    ClientSerializer, ClientListSerializer, ClientCreateSerializer,
    ClientUpdateSerializer,
)
from main.viewsets import BaseModelViewSet
from appointment.serializers import AppointmentDetailSerializer
from appointment.models import Appointment
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from staff.permissions import IsBusinessManager, IsBusinessManagerOrReceptionist
from django_filters import rest_framework as filters
from rest_framework.pagination import PageNumberPagination

class ClientFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='primary_business_id', required=True)
    search = filters.CharFilter(field_name='search', lookup_expr='icontains', required=False, method='filter_search')
    is_active = filters.BooleanFilter(field_name='is_active', required=False)
    is_vip = filters.BooleanFilter(field_name='is_vip', required=False)
    class Meta:
        model = Client
        fields = ['business_id', 'search', 'is_active', 'is_vip']
    
    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(city__icontains=value) |
            Q(state_province__icontains=value) |
            Q(postal_code__icontains=value) |
            Q(country__icontains=value)
        )
    
    
    def filter_is_active(self, queryset, name, value):
        return queryset.filter(is_active=value)
    
    def filter_is_vip(self, queryset, name, value):
        return queryset.filter(is_vip=value)
    
class ClientViewSet(BaseModelViewSet):
    """ViewSet for managing clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, IsBusinessManagerOrReceptionist]
    filterset_class = ClientFilter
    
    def get_queryset(self):
        """Get queryset for clients"""
        print("self.request.user", self.request.user)
        return self.filter_queryset(super().get_queryset())
    

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        self.paginator.page_size = request.query_params.get('page_size', 20)
        page = self.paginate_queryset(queryset)
        
        total_vip_clients = queryset.filter(is_vip=True).count()
        total_clients = queryset.count()
        
        metadata = {
            "total_vip_clients": total_vip_clients,
            "total_clients": total_clients
        }
        
        if page is not None:
            serializer = ClientListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data, metadata=metadata)
        
        serializer = ClientListSerializer(queryset, many=True)
        return self.response_success(serializer.data, metadata=metadata)
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = ClientCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            client = serializer.create(serializer.validated_data)
            return self.response_success(ClientSerializer(client).data)
        except Exception as e:
            return self.response_error(str(e))

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = ClientUpdateSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            client = serializer.update(instance, serializer.validated_data)
            return self.response_success(ClientSerializer(client).data)
        except Exception as e:
            return self.response_error(str(e))
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.is_active = False
            instance.save()
            return self.response_success(ClientSerializer(instance).data, status_code=status.HTTP_200_OK, message="Client deleted successfully")
        except Exception as e:
            return self.response_error(str(e), message="Failed to delete client")

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(city__icontains=query) |
                Q(state_province__icontains=query)
            )
        
        if business_id:
            queryset = queryset.filter(primary_business_id=business_id)
        
        serializer = ClientListSerializer(queryset, many=True)
        return Response(serializer.data)


    # Get booking history for a client
    @action(detail=True, methods=['get'], url_path='booking-history')
    def booking_history(self, request, pk=None):
        """Get booking history for a client."""
        client = self.get_object()
        clients_appointments = Appointment.objects.filter(client=client, is_active=True).order_by('-appointment_date')
        serializer = AppointmentDetailSerializer(clients_appointments, many=True)
        return self.response_success(serializer.data)