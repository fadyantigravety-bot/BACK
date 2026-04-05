from rest_framework import serializers
from .models import PrayerDefinition, PrayerLog


class PrayerDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerDefinition
        fields = ['id', 'name', 'description', 'scheduled_time', 'order',
                  'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrayerLogSerializer(serializers.ModelSerializer):
    prayer_name = serializers.CharField(source='prayer.name', read_only=True)
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = PrayerLog
        fields = ['id', 'member', 'member_name', 'prayer', 'prayer_name', 'date',
                  'status', 'scheduled_time', 'alert_shown_at', 'first_response_at',
                  'followup_sent_at', 'final_response_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class PrayerLogUpdateSerializer(serializers.ModelSerializer):
    """Used by members to update their prayer status."""
    class Meta:
        model = PrayerLog
        fields = ['status', 'alert_shown_at', 'first_response_at',
                  'followup_sent_at', 'final_response_at']
