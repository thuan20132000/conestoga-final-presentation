from rest_framework import viewsets, status, decorators
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification, PushDevice
from .serializers import NotificationSerializer, PushDeviceSerializer
from .services import NotificationDispatcher
from webpush.models import SubscriptionInfo, PushInformation, Group
from main.viewsets import BaseViewSet
from .serializers import PushInformationSerializer, PushGroupSerializer, PushSubscriptionSerializer
dispatcher = NotificationDispatcher()


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["channel", "status", "user"]
    search_fields = ["to", "title", "body"]


class PushDeviceViewSet(viewsets.ModelViewSet):
    queryset = PushDevice.objects.all().order_by("-created_at")
    serializer_class = PushDeviceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["user", "provider", "active"]
    search_fields = ["token"]


class WebPushViewSet(BaseViewSet):
    queryset = PushInformation.objects.all()
    serializer_class = PushInformationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request):
        try:
            subscription, created = SubscriptionInfo.objects.update_or_create(
                endpoint=request.data.get("endpoint"),
                defaults={
                    "auth": request.data.get("auth"),
                    "p256dh": request.data.get("p256dh"),
                    "browser": request.data.get("browser"),
                    "user_agent": request.data.get("user_agent"),
                }
            )
            if created:
                push_information = PushInformation.objects.create(
                    subscription=subscription,
                    user=request.user,
                    group=request.data.get("group"),
                )
            else:
                push_information = PushInformation.objects.filter(subscription=subscription).first()
                
            serializer = PushInformationSerializer(push_information)
            
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
    
    @action(detail=False, methods=["post"], url_path="unsubscribe")
    def unsubscribe(self, request):
        try:
            endpoint = request.data.get("endpoint")
            subscription = SubscriptionInfo.objects.filter(endpoint=endpoint).first()
            print("================= WebPush Unsubscribe subscription:: ", subscription)
            if subscription:
                PushInformation.objects.filter(subscription=subscription).delete()
                subscription.delete()
                
                return self.response_success(data=None, message="Unsubscribed successfully")
            else:
                return self.response_error(data=None, message="Subscription not found")
        except Exception as e:
            return self.response_error(data=None, message=str(e))