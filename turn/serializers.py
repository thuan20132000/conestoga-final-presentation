from rest_framework import serializers
from .models import StaffTurn, Turn, TurnType


class StaffTurnSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    staff_id = serializers.IntegerField(source='staff.id', read_only=True)
    staff_photo = serializers.ImageField(source='staff.photo', read_only=True)

    class Meta:
        model = StaffTurn
        fields = [
            'id',
            'business',
            'staff_id',
            'staff_name',
            'staff_photo',
            'position',
            'date',
            'is_available',
            'joined_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']


class StaffTurnReorderSerializer(serializers.Serializer):
    ordered_staff_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of staff IDs in desired turn order",
    )
    date = serializers.DateField(required=False)


class AssignByServicePriceSerializer(serializers.Serializer):
    service_id = serializers.IntegerField(
        required=False,
        help_text="Service ID — only staff who can perform this service will be considered",
    )
    service_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Service price to determine turn type (>threshold = full, <=threshold = half)",
    )
    date = serializers.DateField(required=False)


class MarkBusySerializer(serializers.Serializer):
    staff_turn_id = serializers.IntegerField()
    service_id = serializers.IntegerField(
        help_text="Service ID for the turn",
        required=False,
    )
    turn_type = serializers.CharField(
        help_text="Turn type (FULL or HALF)",
        required=False,
        default=TurnType.FULL.value,
    )


class CompleteServiceSerializer(serializers.Serializer):
    staff_turn_id = serializers.IntegerField()
    date = serializers.DateField(required=False)


class TurnSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Turn
        fields = [
            'id',
            'service',
            'service_name',
            'service_price',
            'status',
            'in_service_at',
            'turn_type',
            'completed_at',
            'created_at',
        ]


class NextTurnSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    staff_photo = serializers.ImageField(source='staff.photo', read_only=True)

    class Meta:
        model = StaffTurn
        fields = [
            'id',
            'staff_id',
            'staff_name',
            'staff_photo',
            'position',
            'date',
            'is_available',
            'joined_at',
        ]


class JoinedStaffWithHistorySerializer(serializers.ModelSerializer):
    staff_id = serializers.IntegerField(source='staff.id', read_only=True)
    staff_name = serializers.CharField(source='staff.first_name', read_only=True)
    staff_photo = serializers.ImageField(source='staff.photo', read_only=True)
    turns = serializers.SerializerMethodField()

    class Meta:
        model = StaffTurn
        fields = [
            'id',
            'staff_id',
            'staff_name',
            'staff_photo',
            'position',
            'date',
            'is_available',
            'joined_at',
            'turns',
        ]

    def get_turns(self, obj):
        turns = obj.turn.filter(is_deleted=False).order_by('updated_at')
        return TurnSerializer(turns, many=True).data
