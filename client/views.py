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


class ClientViewSet(BaseModelViewSet):
    """ViewSet for managing clients"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    
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

