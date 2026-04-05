from rest_framework import serializers
from .models import ConfessionRecord, ConfessionAttendance
from django.contrib.auth import get_user_model

User = get_user_model()


class ConfessionRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    total_confessions = serializers.IntegerField(read_only=True)

    class Meta:
        model = ConfessionRecord
        fields = ['id', 'member', 'member_name', 'has_confessed', 'last_confession_date',
                  'follow_up_note', 'is_overdue', 'overdue_threshold_days',
                  'recorded_by', 'created_at', 'updated_at', 'total_confessions']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyConfessionAttendanceSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='pk')
    full_name = serializers.CharField()
    phone = serializers.CharField()
    attended = serializers.BooleanField()
    total_confessions = serializers.IntegerField()
