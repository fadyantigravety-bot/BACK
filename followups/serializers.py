from rest_framework import serializers
from .models import FollowUpRecord


class FollowUpRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)
    servant_name = serializers.CharField(source='servant.full_name', read_only=True)

    class Meta:
        model = FollowUpRecord
        fields = ['id', 'member', 'member_name', 'servant', 'servant_name',
                  'type', 'date', 'summary', 'outcome', 'priority', 'status',
                  'next_followup_date', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
