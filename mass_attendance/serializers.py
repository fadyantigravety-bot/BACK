from rest_framework import serializers
from .models import MassAttendanceRecord


class MassAttendanceRecordSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.full_name', read_only=True)

    class Meta:
        model = MassAttendanceRecord
        fields = ['id', 'member', 'member_name', 'date', 'attended',
                  'church_name', 'mass_type', 'notes', 'recorded_by', 'created_at']
        read_only_fields = ['id', 'created_at']
