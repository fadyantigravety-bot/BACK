from rest_framework import serializers
from .models import FridayMeetingSession, FridayAttendanceRecord


class FridayMeetingSessionSerializer(serializers.ModelSerializer):
    total_present = serializers.IntegerField(read_only=True, default=0)
    total_absent = serializers.IntegerField(read_only=True, default=0)
    total_excused = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = FridayMeetingSession
        fields = ['id', 'date', 'title', 'service_stage', 'notes', 'is_locked',
                  'created_by', 'created_at', 'total_present', 'total_absent', 'total_excused']
        read_only_fields = ['id', 'created_at']


class FridayAttendanceRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.full_name', read_only=True, default=None)

    class Meta:
        model = FridayAttendanceRecord
        fields = ['id', 'session', 'member', 'member_name', 'status',
                  'marked_by', 'marked_by_name', 'absence_reason', 'notes',
                  'marked_at', 'updated_at']
        read_only_fields = ['id', 'marked_at', 'updated_at']


class BulkAttendanceSerializer(serializers.Serializer):
    """For quick marking of multiple members at once."""
    records = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1,
    )
    session_id = serializers.UUIDField()

    def validate_records(self, value):
        valid_statuses = ['present', 'absent', 'excused', 'late']
        for record in value:
            if 'member_id' not in record or 'status' not in record:
                raise serializers.ValidationError('كل سجل يجب أن يحتوي على member_id و status')
            if record['status'] not in valid_statuses:
                raise serializers.ValidationError(f'حالة غير صالحة: {record["status"]}')
        return value
