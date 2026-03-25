from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from .models import StaffTurn, Turn, TurnStatus, TurnType, DEFAULT_HALF_TURN_THRESHOLD


class StaffTurnService:

    @staticmethod
    def _get_threshold(business_id):
        """Get the half turn threshold for a business from its settings."""
        from business.models import BusinessSettings
        try:
            settings = BusinessSettings.objects.get(business_id=business_id)
            return settings.half_turn_threshold
        except BusinessSettings.DoesNotExist:
            return Decimal(str(DEFAULT_HALF_TURN_THRESHOLD))

    @staticmethod
    def _get_next_position(business_id, date):
        max_pos = StaffTurn.objects.filter(
            business_id=business_id,
            date=date,
            is_deleted=False,
        ).aggregate(max_pos=models.Max('position'))['max_pos']
        return (max_pos or 0) + 1

    @staticmethod
    @transaction.atomic
    def join_queue(staff, date=None):
        """Add staff to the back of the turn queue.
        If a soft-deleted entry exists for the same day, restore it.
        """
        date = date or timezone.now().date()
        try:
            turn = StaffTurn.objects.get(
                business=staff.business,
                staff=staff,
                date=date,
            )
            # Restore if soft-deleted, or just mark available
            turn.is_deleted = False
            turn.deleted_at = None
            turn.is_available = True
            turn.position = StaffTurnService._get_next_position(
                staff.business_id, date
            )
            turn.save(update_fields=[
                'is_deleted', 'deleted_at', 'is_available',
                'position', 'updated_at',
            ])
            return turn
        except StaffTurn.DoesNotExist:
            return StaffTurn.objects.create(
                business=staff.business,
                staff=staff,
                date=date,
                position=StaffTurnService._get_next_position(
                    staff.business_id, date
                ),
                is_available=True,
            )


    @staticmethod
    @transaction.atomic
    def leave_queue(staff_turn):
        """Remove staff from the turn queue (soft-delete)."""
        staff_turn.is_deleted = True
        staff_turn.deleted_at = timezone.now()
        staff_turn.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
        return staff_turn
    
    @staticmethod
    def get_queue(business_id, date=None):
        """Get the full ordered turn queue for a business on a given date."""
        date = date or timezone.now().date()
        return (
            StaffTurn.objects.filter(
                business_id=business_id,
                date=date,
                is_deleted=False,
            )
            .select_related('staff')
            .order_by('position')
        )

    @staticmethod
    def get_joined_staffs(business_id, date=None):
        """Get the turn queue with each staff's turn records for the day."""
        date = date or timezone.now().date()
        return (
            StaffTurn.objects.filter(
                business_id=business_id,
                date=date,
                is_deleted=False,
            )
            .select_related('staff')
            .prefetch_related('turn__service')
            .order_by('joined_at')
        )

    @staticmethod
    def _get_eligible_staff_ids(service_id):
        """Get staff IDs who can perform a given service."""
        from staff.models import StaffService
        return list(
            StaffService.objects.filter(
                service_id=service_id,
                is_active=True,
                is_deleted=False,
            ).values_list('staff_id', flat=True)
        )

    @staticmethod
    def get_next_available(business_id, date=None, service_id=None):
        """Get the next available staff member in the queue.
        If service_id is provided, only considers staff who can perform that service.
        """
        date = date or timezone.now().date()
        qs = StaffTurn.objects.filter(
            business_id=business_id,
            date=date,
            is_deleted=False,
            is_available=True,
        )
        if service_id:
            eligible_ids = StaffTurnService._get_eligible_staff_ids(service_id)
            qs = qs.filter(staff_id__in=eligible_ids)
        return qs.select_related('staff').order_by('position')

    @staticmethod
    @transaction.atomic
    def send_to_back(staff, date=None):
        """Move a staff member to the back of the queue after finishing service."""
        date = date or timezone.now().date()
        try:
            turn = StaffTurn.objects.select_for_update().get(
                business=staff.business,
                staff=staff,
                date=date,
                is_deleted=False,
            )
        except StaffTurn.DoesNotExist:
            raise ValueError("Staff is not in the turn queue")

        turn.position = StaffTurnService._get_next_position(
            staff.business_id, date
        )
        turn.is_available = True
        turn.save(update_fields=[
                  'position', 'is_available', 'updated_at'])
        return turn

    @staticmethod
    @transaction.atomic
    def send_to_top(staff, date=None):
        """Move a staff member to the top of the queue."""
        date = date or timezone.now().date()
        try:
            turn = StaffTurn.objects.select_for_update().get(
                business=staff.business,
                staff=staff,
                date=date,
                is_deleted=False,
            )
        except StaffTurn.DoesNotExist:
            raise ValueError("Staff is not in the turn queue")

        turn.position = 1
        turn.save(update_fields=['position', 'is_available', 'updated_at'])
        return turn

    @staticmethod
    @transaction.atomic
    def mark_in_service(business_id, staff_turn_id, service_id=None, service_price=None, turn_type=None, date=None):
        """Mark a staff member as in service and create a Turn record.

        FULL turn: staff becomes unavailable (busy serving).
        HALF turn: staff stays available and keeps position.
        """
        date = date or timezone.now().date()
        try:
            staff_turn = StaffTurn.objects.select_for_update().get(
                business_id=business_id,
                id=staff_turn_id,
                date=date,
                is_deleted=False,
            )
        except StaffTurn.DoesNotExist:
            raise ValueError("Staff is not in the turn queue")

        turn_type = turn_type or TurnType.FULL.value

        # HALF turn: staff stays available and keeps position
        # FULL turn: staff becomes unavailable
        if turn_type != TurnType.HALF.value:
            staff_turn.is_available = False
            staff_turn.save(update_fields=['is_available', 'updated_at'])

        # Create a Turn record
        turn = Turn.objects.create(
            staff_turn=staff_turn,
            service_id=service_id,
            service_price=service_price or 0,
            status=TurnStatus.IN_SERVICE,
            in_service_at=timezone.now(),
            turn_type=turn_type,
        )
        return turn

    @staticmethod
    @transaction.atomic
    def mark_available(staff, date=None):
        """Mark a staff member as available."""
        date = date or timezone.now().date()
        StaffTurn.objects.filter(
            business=staff.business,
            staff=staff,
            date=date,
            is_deleted=False,
        ).update(is_available=True)

    @staticmethod
    @transaction.atomic
    def reorder_queue(business_id, ordered_staff_ids, date=None):
        """Manually reorder the queue. ordered_staff_ids is a list of staff IDs in desired order."""
        date = date or timezone.now().date()
        turns = StaffTurn.objects.filter(
            business_id=business_id,
            date=date,
            is_deleted=False,
        ).select_for_update()

        turn_map = {str(t.staff_id): t for t in turns}
        for idx, staff_id in enumerate(ordered_staff_ids, start=1):
            staff_id_str = str(staff_id)
            if staff_id_str in turn_map:
                turn = turn_map[staff_id_str]
                turn.position = idx
                turn.save(update_fields=['position', 'updated_at'])

    @staticmethod
    @transaction.atomic
    def skip_turn(staff, date=None):
        """Skip a staff member's turn — swap them with the next person in line."""
        date = date or timezone.now().date()
        try:
            turn = StaffTurn.objects.select_for_update().get(
                business=staff.business,
                staff=staff,
                date=date,
                is_deleted=False,
            )
        except StaffTurn.DoesNotExist:
            raise ValueError("Staff is not in the turn queue")

        next_turn = (
            StaffTurn.objects.select_for_update()
            .filter(
                business=staff.business,
                date=date,
                is_deleted=False,
                position__gt=turn.position,
            )
            .order_by('position')
            .first()
        )

        if next_turn:
            turn.position, next_turn.position = next_turn.position, turn.position
            turn.save(update_fields=['position', 'updated_at'])
            next_turn.save(update_fields=['position', 'updated_at'])

        return turn

    @staticmethod
    def get_turn_type(service_price, business_id=None):
        """Determine turn type based on service price and business threshold.
        Price > threshold → FULL turn, otherwise → HALF turn.
        """
        if business_id:
            threshold = StaffTurnService._get_threshold(business_id)
        else:
            threshold = Decimal(str(DEFAULT_HALF_TURN_THRESHOLD))
        if Decimal(str(service_price)) > threshold:
            return TurnType.FULL
        return TurnType.HALF

    @staticmethod
    def get_next_turns(business_id, service_id=None, service_price=None, date=None):
        """Get the next staff member who should serve, based on service price.

        Full turn (price > threshold): first available staff (front of queue).
        Half turn (price <= threshold): last available staff (back of queue).
        No price provided: returns first available (front of queue).

        Returns a dict with the StaffTurn and the turn_type, or None.
        """
        date = date or timezone.now().date()

        nt = StaffTurn.objects.filter(
            business_id=business_id,
            date=date,
            is_deleted=False,
            is_available=True,
        )
        if service_id:
            eligible_ids = StaffTurnService._get_eligible_staff_ids(service_id)
            nt = nt.filter(staff_id__in=eligible_ids)
            
        return nt.select_related('staff').order_by('position').all()

    @staticmethod
    def get_last_available(business_id, date=None, service_id=None):
        """Get the last available staff member in the queue (for half turns).
        If service_id is provided, only considers staff who can perform that service.
        """
        date = date or timezone.now().date()
        qs = StaffTurn.objects.filter(
            business_id=business_id,
            date=date,
            is_deleted=False,
            is_available=True,
        )
        if service_id:
            eligible_ids = StaffTurnService._get_eligible_staff_ids(service_id)
            qs = qs.filter(staff_id__in=eligible_ids)
        return qs.select_related('staff').order_by('-position').first()

    @staticmethod
    @transaction.atomic
    def complete_service(business_id, staff_turn_id, date=None):
        """Complete a service and update queue position based on turn type.

        Full turn: staff goes to the back of the queue and becomes available.
        Half turn: staff stays in current position (was never marked unavailable).
        """
        date = date or timezone.now().date()
        try:
            staff_turn = StaffTurn.objects.select_for_update().get(
                business_id=business_id,
                id=staff_turn_id,
                date=date,
                is_deleted=False,
            )
        except StaffTurn.DoesNotExist:
            raise ValueError("Staff is not in the turn queue")

        # Mark the latest in-service Turn as completed
        latest_turn = (
            Turn.objects.filter(
                staff_turn=staff_turn,
                status=TurnStatus.IN_SERVICE,
                is_deleted=False,
            )
            .order_by('-created_at')
            .first()
        )

        turn_type = latest_turn.turn_type if latest_turn else TurnType.FULL.value

        if latest_turn:
            latest_turn.status = TurnStatus.COMPLETED
            latest_turn.completed_at = timezone.now()
            latest_turn.save(update_fields=['status', 'completed_at', 'updated_at'])

        # FULL turn: send to back and mark available
        # HALF turn: position unchanged, staff was already available
        if turn_type == TurnType.FULL.value:
            staff_turn.position = StaffTurnService._get_next_position(
                business_id, date
            )
            staff_turn.is_available = True
            staff_turn.save(update_fields=['position', 'is_available', 'updated_at'])

        return staff_turn

    @staticmethod
    def get_completed_turns(business_id, date=None):
        """Get all completed turns for a business, grouped by staff with individual turn records."""
        date = date or timezone.now().date()
        turns = (
            Turn.objects.filter(
                staff_turn__business_id=business_id,
                staff_turn__date=date,
                status=TurnStatus.COMPLETED,
                is_deleted=False,
            )
            .select_related('staff_turn__staff', 'service')
            .order_by('completed_at')
        )

        staff_map = {}
        for t in turns:
            sid = str(t.staff_turn.staff_id)
            if sid not in staff_map:
                staff = t.staff_turn.staff
                staff_map[sid] = {
                    'staff_id': t.staff_turn.staff_id,
                    'staff_name': staff.get_full_name(),
                    'staff_photo': staff.photo.url if staff.photo else None,
                    'total_turns': 0,
                    'full_turns': 0,
                    'half_turns': 0,
                    'turns': [],
                }
            entry = staff_map[sid]
            entry['total_turns'] += 1
            turn_type = StaffTurnService.get_turn_type(
                t.service_price, business_id
            )
            if turn_type == TurnType.FULL:
                entry['full_turns'] += 1
            else:
                entry['half_turns'] += 1
            entry['turns'].append(t)

        return list(staff_map.values())

    @staticmethod
    def check_if_staff_is_in_service(staff_turn, date=None):
        """Check if a staff turn is in service."""
        date = date or timezone.now().date()
        return staff_turn.turn.filter(
            staff_turn=staff_turn,
            in_service_at__date=date,
            status=TurnStatus.IN_SERVICE,
            is_deleted=False,
        ).exists()