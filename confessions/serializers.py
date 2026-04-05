from rest_framework import serializers
from .models import ConfessionRecord


class ConfessionRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = ConfessionRecord
        fields = ['id', 'member', 'member_name', 'has_confessed', 'last_confession_date',
                  'follow_up_note', 'is_overdue', 'overdue_threshold_days',
                  'recorded_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
