from rest_framework import viewsets
from core.permissions import IsPriest
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Priest-only audit log viewer."""
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsPriest]
    filterset_fields = ['action', 'target_type', 'user']
    search_fields = ['action', 'target_type']
    ordering_fields = ['created_at']
