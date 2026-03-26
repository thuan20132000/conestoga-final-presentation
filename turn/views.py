from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_filters import rest_framework as filters

from main.viewsets import BaseModelViewSet
from staff.models import Staff
from staff.permissions import IsBusinessManagerOrReceptionist
from .models import StaffTurn
from .serializers import (
    CompleteServiceSerializer,
    JoinedStaffWithHistorySerializer,
    MarkBusySerializer,
    NextTurnSerializer,
    StaffTurnReorderSerializer,
    StaffTurnSerializer,
    TurnSerializer,
    UpdateTurnSerializer,
)
from .services import StaffTurnService


class StaffTurnFilter(filters.FilterSet):
    business_id = filters.UUIDFilter(field_name='business_id', required=True)
    date = filters.DateFilter(field_name='date', required=False)

    class Meta:
        model = StaffTurn
        fields = ['business_id', 'date']


class StaffTurnViewSet(BaseModelViewSet):
    """ViewSet for staff turn queue management."""

    queryset = StaffTurn.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, IsBusinessManagerOrReceptionist]
    filterset_class = StaffTurnFilter
    serializer_class = StaffTurnSerializer

    def _get_business_id(self, request):
        return request.query_params.get('business_id') or request.user.business_id

    def list(self, request, *args, **kwargs):
        """Get the turn queue for a business. Defaults to today."""
        try:
            business_id = self._get_business_id(request)
            date_str = request.query_params.get('date')
            date = date_str or timezone.now().date()
            queue = StaffTurnService.get_queue(business_id=business_id, date=date)
            serializer = StaffTurnSerializer(queue, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['get'], url_path='joined')
    def joined_staffs(self, request):
        """Get all joined staff with their turn history for the day."""
        try:
            business_id = self._get_business_id(request)
            date_str = request.query_params.get('date')
            date = date_str or timezone.now().date()
            results = StaffTurnService.get_joined_staffs(
                business_id=business_id, date=date
            )
            joined_staffs = JoinedStaffWithHistorySerializer(results, many=True).data
            return self.response_success(joined_staffs)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['get'], url_path='next')
    def next_available_staffs(self, request):
        """Get the next available staff in the turn queue.
        Optionally filter by service_id to only return staff who can perform that service.
        """
        try:
            business_id = self._get_business_id(request)
            date_str = request.query_params.get('date')
            date = date_str or timezone.now().date()
            service_id = request.query_params.get('service_id')

            turns = StaffTurnService.get_next_available(
                business_id=business_id, date=date, service_id=service_id
            )
            if not turns:
                return self.response_success(None, message="No available staff in queue")
            return self.response_success(StaffTurnSerializer(turns, many=True).data)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['get'], url_path='next-turns')
    def next_turn(self, request):
        """Get the next staff who should serve based on service price.
        Full turn (price > threshold): first available (front of queue).
        Half turn (price <= threshold): last available (back of queue).
        No price: defaults to first available.
        """
        try:
            business_id = self._get_business_id(request)
            date_str = request.query_params.get('date')
            date = date_str or timezone.now().date()
            service_id = request.query_params.get('service_id')
            service_price = request.query_params.get('service_price')

            result = StaffTurnService.get_next_turns(
                business_id=business_id,
                service_id=service_id,
                service_price=service_price,
                date=date,
            )
            if not result:
                return self.response_success(None, message="No available staff in queue")
            
            next_turns = NextTurnSerializer(result, many=True).data
            
            return self.response_success(next_turns)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='send-to-back')
    def send_to_back(self, request):
        """Move a staff to the back of the queue after they finish serving."""
        try:
            staff_id = request.data.get('staff_id')
            staff = Staff.objects.get(
                id=staff_id, business_id=self._get_business_id(request)
            )
            turn = StaffTurnService.send_to_back(staff)
            return self.response_success(StaffTurnSerializer(turn).data)
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))
        
    @action(detail=False, methods=['post'], url_path='send-to-top')
    def send_to_top(self, request):
        """Move a staff to the top of the queue."""
        try:
            staff_id = request.data.get('staff_id')
            staff = Staff.objects.get(
                id=staff_id, business_id=self._get_business_id(request)
            )
            turn = StaffTurnService.send_to_top(staff)
            return self.response_success(StaffTurnSerializer(turn).data)
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='mark-in-service')
    def mark_in_service(self, request):
        """Mark a staff as in service (currently serving).
        Creates a Turn record linked to the service.
        """
        try:
            serializer = MarkBusySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            business_id = self._get_business_id(request)
            turn_type = serializer.validated_data.get('turn_type', None)
            is_client_request = serializer.validated_data.get('is_client_request', False)
            turn = StaffTurnService.mark_in_service(
                business_id=business_id,
                staff_turn_id=serializer.validated_data.get('staff_turn_id'),
                service_id=serializer.validated_data.get('service_id'),
                service_price=serializer.validated_data.get('service_price'),
                turn_type=turn_type,
                date=serializer.validated_data.get('date'),
                is_client_request=is_client_request,
            )
            return self.response_success(
                TurnSerializer(turn).data,
                message="Staff marked as in service",
            )
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        """Manually reorder the entire queue."""
        try:
            serializer = StaffTurnReorderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            business_id = self._get_business_id(request)
            date = serializer.validated_data.get('date', timezone.now().date())
            StaffTurnService.reorder_queue(
                business_id=business_id,
                ordered_staff_ids=serializer.validated_data['ordered_staff_ids'],
                date=date,
            )
            queue = StaffTurnService.get_queue(business_id, date)
            return self.response_success(StaffTurnSerializer(queue, many=True).data)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='skip')
    def skip_turn(self, request):
        """Skip a staff member's turn (move them one position back)."""
        try:
            staff_id = request.data.get('staff_id')
            staff = Staff.objects.get(
                id=staff_id, business_id=self._get_business_id(request)
            )
            turn = StaffTurnService.skip_turn(staff)
            return self.response_success(StaffTurnSerializer(turn).data)
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='join')
    def join_queue(self, request):
        """Manually add a staff to the turn queue."""
        try:
            staff_id = request.data.get('staff_id')
            date = request.data.get('date', timezone.now().date())
            staff = Staff.objects.get(
                id=staff_id, business_id=self._get_business_id(request)
            )
            turn = StaffTurnService.join_queue(staff, date=date)
            return self.response_success(StaffTurnSerializer(turn).data)
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='leave')
    def leave_queue(self, request):
        """Manually remove a staff from the turn queue."""
        try:
            staff_turn_id = request.data.get('staff_turn_id')
            date = request.data.get('date', timezone.now().date())
            print("staff_turn_id:: ", staff_turn_id)
            print("date:: ", date)
            staff_turn = StaffTurn.objects.get(
                business_id=self._get_business_id(request),
                id=staff_turn_id,
                date=date,
                is_deleted=False,
            )
            print("staff_turn:: ", staff_turn.__dict__)
            in_service = StaffTurnService.check_if_staff_is_in_service(staff_turn, date=date)
            if in_service:
                return self.response_error(
                    data=None,
                    message="Staff is in service, please complete the service first"
                )
            
            print("leaving queue ... ")
            StaffTurnService.leave_queue(staff_turn=staff_turn)
            return self.response_success(None, message="Staff removed from queue")
        except Exception as e:
            print("error:: ", e)
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='update-turn')
    def update_turn(self, request):
        """Update an existing turn's details (service, price, turn type, client request)."""
        try:
            serializer = UpdateTurnSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            turn_id = data.pop('turn_id')
            turn = StaffTurnService.update_turn(turn_id=turn_id, **data)
            return self.response_success(TurnSerializer(turn).data)
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['post'], url_path='complete-service')
    def complete_service(self, request):
        """Complete a service and update queue position.
        Uses the turn type stored when staff was marked busy.
        """
        try:
            serializer = CompleteServiceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            business_id = self._get_business_id(request)
            date = serializer.validated_data.get('date', timezone.now().date())
            staff_turn_id = serializer.validated_data.get('staff_turn_id')
            turn = StaffTurnService.complete_service(
                business_id=business_id,
                staff_turn_id=staff_turn_id,
                date=date,
            )
            return self.response_success(StaffTurnSerializer(turn).data)
        except Staff.DoesNotExist:
            return self.response_error("Staff not found")
        except Exception as e:
            return self.response_error(str(e))

    @action(detail=False, methods=['get'], url_path='completed')
    def completed_turns(self, request):
        """Get all completed turns grouped by staff, with individual turn records."""
        try:
            business_id = self._get_business_id(request)
            date_str = request.query_params.get('date')
            date = date_str or timezone.now().date()
            results = StaffTurnService.get_completed_turns(
                business_id=business_id, date=date
            )
            data = [
                {
                    'staff_id': r['staff_id'],
                    'staff_name': r['staff_name'],
                    'staff_photo': r['staff_photo'],
                    'total_turns': r['total_turns'],
                    'full_turns': r['full_turns'],
                    'half_turns': r['half_turns'],
                    'turns': TurnSerializer(r['turns'], many=True).data,
                }
                for r in results
            ]
            return self.response_success(data)
        except Exception as e:
            return self.response_error(str(e))
