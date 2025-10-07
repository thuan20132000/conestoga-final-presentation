from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.shortcuts import get_object_or_404

from .models import Client, ClientHistory, ClientPreference
from .serializers import (
    ClientSerializer, ClientListSerializer, ClientCreateSerializer,
    ClientUpdateSerializer, ClientHistorySerializer, ClientPreferenceSerializer,
    ClientStatsSerializer
)
from business.models import Business


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for managing clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['email', 'phone', 'is_active', 'is_vip', 'primary_business']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'city', 'state_province']
    ordering_fields = ['first_name', 'last_name', 'created_at', 'email']
    ordering = ['last_name', 'first_name']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ClientListSerializer
        elif self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientUpdateSerializer
        return ClientSerializer
    
    def get_queryset(self):
        """Filter clients by business if specified"""
        queryset = super().get_queryset()
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(primary_business_id=business_id)
        return queryset

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get client history"""
        client = self.get_object()
        history = client.history.all()[:50]  # Limit to last 50 entries
        serializer = ClientHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def preferences(self, request, pk=None):
        """Get or update client preferences"""
        client = self.get_object()
        
        if request.method == 'GET':
            preferences = client.preferences.all()
            serializer = ClientPreferenceSerializer(preferences, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            data = request.data.copy()
            data['client'] = client.id
            serializer = ClientPreferenceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_preference(self, request, pk=None):
        """Add a new preference for the client"""
        client = self.get_object()
        data = request.data.copy()
        data['client'] = client.id
        
        serializer = ClientPreferenceSerializer(data=data)
        if serializer.is_valid():
            preference, created = ClientPreference.objects.get_or_create(
                client=client,
                preference_type=data.get('preference_type'),
                preference_key=data.get('preference_key'),
                defaults={'preference_value': data.get('preference_value')}
            )
            if not created:
                preference.preference_value = data.get('preference_value')
                preference.save()
            
            serializer = ClientPreferenceSerializer(preference)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get client statistics"""
        queryset = self.get_queryset()
        
        # Basic stats
        total_clients = queryset.count()
        active_clients = queryset.filter(is_active=True).count()
        vip_clients = queryset.filter(is_vip=True).count()
        
        # New clients this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_clients_this_month = queryset.filter(created_at__gte=start_of_month).count()
        
        # Clients by business
        clients_by_business = dict(
            queryset.values('primary_business__name')
            .annotate(count=Count('id'))
            .values_list('primary_business__name', 'count')
        )
        
        # Clients by preferred contact method
        clients_by_preferred_contact = dict(
            queryset.values('preferred_contact_method')
            .annotate(count=Count('id'))
            .values_list('preferred_contact_method', 'count')
        )
        
        stats_data = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'vip_clients': vip_clients,
            'new_clients_this_month': new_clients_this_month,
            'clients_by_business': clients_by_business,
            'clients_by_preferred_contact': clients_by_preferred_contact,
        }
        
        serializer = ClientStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced client search"""
        query = request.query_params.get('q', '')
        business_id = request.query_params.get('business')
        
        queryset = self.get_queryset()
        
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

    @action(detail=True, methods=['post'])
    def toggle_vip(self, request, pk=None):
        """Toggle VIP status for a client"""
        client = self.get_object()
        client.is_vip = not client.is_vip
        client.save()
        
        # Create history entry
        ClientHistory.objects.create(
            client=client,
            action='vip_toggled',
            description=f"VIP status {'enabled' if client.is_vip else 'disabled'}",
            changed_by=request.user
        )
        
        serializer = self.get_serializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status for a client"""
        client = self.get_object()
        client.is_active = not client.is_active
        client.save()
        
        # Create history entry
        ClientHistory.objects.create(
            client=client,
            action='status_changed',
            description=f"Client {'activated' if client.is_active else 'deactivated'}",
            changed_by=request.user
        )
        
        serializer = self.get_serializer(client)
        return Response(serializer.data)


class ClientPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing client preferences"""
    queryset = ClientPreference.objects.all()
    serializer_class = ClientPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter preferences by client if specified"""
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset


class ClientHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing client history"""
    queryset = ClientHistory.objects.all()
    serializer_class = ClientHistorySerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-changed_at']
    
    def get_queryset(self):
        """Filter history by client if specified"""
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset