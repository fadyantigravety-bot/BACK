from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'target_type',
                  'target_id', 'details', 'ip_address', 'created_at']
