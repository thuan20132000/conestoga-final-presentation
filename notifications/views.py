from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification, PushDevice
from .serializers import NotificationSerializer, PushDeviceSerializer
from .services import NotificationDispatcher


dispatcher = NotificationDispatcher()


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["channel", "status", "user"]
    search_fields = ["to", "title", "body"]

    @decorators.action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        notification = self.get_object()
        if notification.status == Notification.Status.SENT:
            return Response({"detail": "Already sent"}, status=status.HTTP_400_BAD_REQUEST)

        result = dispatcher.dispatch(
            channel=notification.channel,
            to=notification.to,
            title=notification.title,
            body=notification.body,
            data=notification.data or {},
        )
        if result.ok:
            notification.mark_sent()
            return Response({"detail": "Sent"}, status=status.HTTP_200_OK)
        notification.mark_failed(result.error or "Unknown error")
        return Response({"detail": result.error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PushDeviceViewSet(viewsets.ModelViewSet):
    queryset = PushDevice.objects.all().order_by("-created_at")
    serializer_class = PushDeviceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["user", "provider", "active"]
    search_fields = ["token"]
