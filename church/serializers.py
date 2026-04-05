from rest_framework import serializers
from .models import ServiceStage, ServiceGroup


class ServiceStageSerializer(serializers.ModelSerializer):
    groups_count = serializers.IntegerField(source='groups.count', read_only=True)

    class Meta:
        model = ServiceStage
        fields = ['id', 'name', 'description', 'order', 'is_active', 'groups_count', 'created_at']


class ServiceGroupSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    leader_name = serializers.CharField(source='leader.full_name', read_only=True, default=None)
    members_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = ServiceGroup
        fields = ['id', 'name', 'stage', 'stage_name', 'leader', 'leader_name',
                  'is_active', 'members_count', 'created_at']
