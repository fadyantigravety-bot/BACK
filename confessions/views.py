from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsPriest
from .models import ConfessionRecord
from .serializers import ConfessionRecordSerializer
from audit.services import log_action


class ConfessionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ConfessionRecordSerializer
    filterset_fields = ['member', 'has_confessed', 'is_overdue']
    search_fields = ['member__first_name', 'member__last_name']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'priest':
            return ConfessionRecord.objects.select_related('member').all()
        if user.role == 'service_leader':
            try:
                if user.serviceleaderprofile.can_view_confession_status:
                    from core.scoping import get_scoped_member_users
                    member_ids = get_scoped_member_users(user)
                    return ConfessionRecord.objects.filter(member_id__in=member_ids)
            except Exception:
                pass
        return ConfessionRecord.objects.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPriest()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save(recorded_by=self.request.user)
        log_action(self.request.user, 'confession_marked', 'ConfessionRecord',
                   instance.id, {'member_id': str(instance.member_id)})

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, 'confession_updated', 'ConfessionRecord',
                   instance.id, {'member_id': str(instance.member_id)})
