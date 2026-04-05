from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsPriest, IsPriestOrServiceLeader
from .models import ServiceStage, ServiceGroup
from .serializers import ServiceStageSerializer, ServiceGroupSerializer


class ServiceStageViewSet(viewsets.ModelViewSet):
    queryset = ServiceStage.objects.all()
    serializer_class = ServiceStageSerializer
    search_fields = ['name']
    filterset_fields = ['is_active']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPriest()]
        return [IsAuthenticated()]


class ServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = ServiceGroup.objects.select_related('stage', 'leader').all()
    serializer_class = ServiceGroupSerializer
    search_fields = ['name']
    filterset_fields = ['stage', 'is_active']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPriestOrServiceLeader()]
        return [IsAuthenticated()]
