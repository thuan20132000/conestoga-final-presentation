from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsOwnerOrReadOnly, IsBusinessOwner, IsAuthenticatedOrReadOnly, AnalyticsPermission, ExportPermission
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Business, AIConfiguration, CallSession, ConversationMessage,
    Intent, AudioRecording, SystemLog
)
from .serializers import (
    BusinessSerializer, BusinessDetailSerializer, AIConfigurationSerializer,
    CallSessionSerializer, CallSessionDetailSerializer, ConversationMessageSerializer,
    IntentSerializer, AudioRecordingSerializer, SystemLogSerializer,
    CallStatisticsSerializer, BusinessStatisticsSerializer, IntentStatisticsSerializer,
    APIResponseSerializer
)
from .filters import (
    CallSessionFilter, ConversationMessageFilter, IntentFilter,
    SystemLogFilter, BusinessFilter
)
from main.viewsets import BaseModelViewSet


class BusinessViewSet(BaseModelViewSet):
    """ViewSet for Business model with CRUD operations."""

    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BusinessFilter
    search_fields = ['name', 'phone_number', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return BusinessDetailSerializer
        return BusinessSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a specific business."""
        business = self.get_object()

        # Get call statistics
        calls = business.calls.all()
        total_calls = calls.count()
        completed_calls = calls.filter(status='completed').count()
        failed_calls = calls.filter(status='failed').count()
        in_progress_calls = calls.filter(status='in_progress').count()

        # Calculate durations
        completed_call_durations = calls.filter(
            status='completed').values_list('duration_seconds', flat=True)
        average_duration = sum(completed_call_durations) / \
            len(completed_call_durations) if completed_call_durations else 0
        total_duration = sum(completed_call_durations)

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_calls = calls.filter(
            started_at__gte=week_ago).order_by('-started_at')[:10]

        stats_data = {
            'business': business,
            'total_calls': total_calls,
            'completed_calls': completed_calls,
            'failed_calls': failed_calls,
            'average_duration': round(average_duration, 2),
            'total_duration': total_duration,
            'recent_activity': CallSessionSerializer(recent_calls, many=True).data
        }

        serializer = BusinessStatisticsSerializer(stats_data)
        return self.response_success(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics for all businesses."""
        businesses = self.get_queryset()
        analytics_data = []

        for business in businesses:
            calls = business.calls.all()
            total_calls = calls.count()
            completed_calls = calls.filter(status='completed').count()

            # Calculate average duration
            completed_call_durations = calls.filter(
                status='completed').values_list('duration_seconds', flat=True)
            average_duration = sum(completed_call_durations) / len(
                completed_call_durations) if completed_call_durations else 0

            analytics_data.append({
                'business': business,
                'total_calls': total_calls,
                'completed_calls': completed_calls,
                'average_duration': round(average_duration, 2)
            })

        serializer = BusinessStatisticsSerializer(analytics_data, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='ai-config')
    def ai_config(self, request, pk=None):
        """Get health status."""
        object = self.get_object()
        ai_configurations = object.ai_config
        serializer = AIConfigurationSerializer(ai_configurations)
        print("Serializer data:: ", serializer.data)
        return self.response_success(serializer.data)

class AIConfigurationViewSet(BaseModelViewSet):
    """ViewSet for AIConfiguration model."""

    queryset = AIConfiguration.objects.all()
    serializer_class = AIConfigurationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ai_name', 'model_name', 'language']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


class CallSessionViewSet(BaseModelViewSet):
    """ViewSet for CallSession model."""

    queryset = CallSession.objects.all()
    serializer_class = CallSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CallSessionFilter
    search_fields = ['call_sid', 'caller_number', 'transcript_summary']
    ordering_fields = ['started_at', 'duration_seconds', 'status']
    ordering = ['-started_at']

    def get_serializer_class(self):
        """Return detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return CallSessionDetailSerializer
        return CallSessionSerializer

    @action(detail=True, methods=['get'])
    def transcript(self, request, pk=None):
        """Get full transcript for a call session."""
        call = self.get_object()
        messages = call.messages.all().order_by('timestamp')

        transcript_data = {
            'call_sid': call.call_sid,
            'business': call.business.name,
            'started_at': call.started_at,
            'duration': call.duration_formatted,
            'status': call.status,
            'messages': ConversationMessageSerializer(messages, many=True).data
        }

        return self.response_success(transcript_data)

    @action(detail=True, methods=['get'])
    def intents(self, request, pk=None):
        """Get all intents for a call session."""
        call = self.get_object()
        intents = call.intents.all().order_by('created_at')
        serializer = IntentSerializer(intents, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'])
    def recordings(self, request, pk=None):
        """Get all recordings for a call session."""
        call = self.get_object()
        recordings = call.recordings.all()
        serializer = AudioRecordingSerializer(recordings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get all logs for a call session."""
        call = self.get_object()
        logs = call.logs.all().order_by('created_at')
        serializer = SystemLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall call statistics."""
        calls = self.get_queryset()

        total_calls = calls.count()
        completed_calls = calls.filter(status='completed').count()
        failed_calls = calls.filter(status='failed').count()
        in_progress_calls = calls.filter(status='in_progress').count()

        # Calculate average duration
        completed_call_durations = calls.filter(
            status='completed').values_list('duration_seconds', flat=True)
        average_duration = sum(completed_call_durations) / \
            len(completed_call_durations) if completed_call_durations else 0
        total_duration = sum(completed_call_durations)

        # Calls by status
        calls_by_status = dict(calls.values('status').annotate(
            count=Count('id')).values_list('status', 'count'))

        # Calls by day (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_calls = calls.filter(started_at__gte=thirty_days_ago)
        calls_by_day = {}
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            day_calls = recent_calls.filter(
                started_at__gte=day_start, started_at__lt=day_end).count()
            calls_by_day[day_start.strftime('%Y-%m-%d')] = day_calls

        stats_data = {
            'total_calls': total_calls,
            'completed_calls': completed_calls,
            'failed_calls': failed_calls,
            'in_progress_calls': in_progress_calls,
            'average_duration': round(average_duration, 2),
            'total_duration': total_duration,
            'calls_by_status': calls_by_status,
            'calls_by_day': calls_by_day
        }

        serializer = CallStatisticsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active (in-progress) calls."""
        active_calls = self.get_queryset().filter(status='in_progress')
        serializer = self.get_serializer(active_calls, many=True)
        return Response(serializer.data)


class ConversationMessageViewSet(BaseModelViewSet):
    """ViewSet for ConversationMessage model."""

    queryset = ConversationMessage.objects.all()
    serializer_class = ConversationMessageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ConversationMessageFilter
    search_fields = ['content']
    ordering_fields = ['timestamp', 'role']
    ordering = ['timestamp']

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get messages filtered by role."""
        role = request.query_params.get('role')
        if role:
            messages = self.get_queryset().filter(role=role)
            serializer = self.get_serializer(messages, many=True)
            return Response(serializer.data)
        return Response({'error': 'Role parameter is required'}, status=status.HTTP_400_BAD_REQUEST)


class IntentViewSet(BaseModelViewSet):
    """ViewSet for Intent model."""

    queryset = Intent.objects.all()
    serializer_class = IntentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = IntentFilter
    search_fields = ['name']
    ordering_fields = ['confidence', 'created_at', 'name']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get intent statistics."""
        intents = self.get_queryset()

        # Group by intent name
        intent_stats = {}
        for intent in intents:
            name = intent.name
            if name not in intent_stats:
                intent_stats[name] = {
                    'count': 0,
                    'confidences': [],
                    'successful_calls': 0
                }

            intent_stats[name]['count'] += 1
            intent_stats[name]['confidences'].append(intent.confidence)

            # Count successful calls (where call status is completed)
            if intent.call.status == 'completed':
                intent_stats[name]['successful_calls'] += 1

        # Calculate averages and success rates
        statistics_data = []
        for name, stats in intent_stats.items():
            avg_confidence = sum(stats['confidences']) / \
                len(stats['confidences'])
            success_rate = (stats['successful_calls'] /
                            stats['count']) * 100 if stats['count'] > 0 else 0

            statistics_data.append({
                'intent_name': name,
                'count': stats['count'],
                'average_confidence': round(avg_confidence, 2),
                'success_rate': round(success_rate, 2)
            })

        serializer = IntentStatisticsSerializer(statistics_data, many=True)
        return self.response_success(
            serializer.data
        )


class AudioRecordingViewSet(BaseModelViewSet):
    """ViewSet for AudioRecording model."""

    queryset = AudioRecording.objects.all()
    serializer_class = AudioRecordingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'duration_seconds']
    ordering = ['-created_at']


class SystemLogViewSet(BaseModelViewSet):
    """ViewSet for SystemLog model."""

    queryset = SystemLog.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SystemLogFilter
    search_fields = ['message']
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get logs filtered by level."""
        level = request.query_params.get('level')
        if level:
            logs = self.get_queryset().filter(level=level)
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response({'error': 'Level parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def errors(self, request):
        """Get all error logs."""
        error_logs = self.get_queryset().filter(level='error')
        serializer = self.get_serializer(error_logs, many=True)
        return Response(serializer.data)
