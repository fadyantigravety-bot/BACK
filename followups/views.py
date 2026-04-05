from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsLeadership
from core.scoping import get_scoped_member_users
from .models import FollowUpRecord
from .serializers import FollowUpRecordSerializer


class FollowUpRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpRecordSerializer
    filterset_fields = ['member', 'servant', 'type', 'priority', 'status']
    search_fields = ['summary', 'member__first_name', 'member__last_name']
    ordering_fields = ['date', 'priority', 'status', 'next_followup_date']

    def get_queryset(self):
        user = self.request.user
        qs = FollowUpRecord.objects.select_related('member', 'servant', 'created_by')
        if user.role == 'priest':
            return qs
        if user.role in ('service_leader', 'servant'):
            member_ids = get_scoped_member_users(user)
            return qs.filter(member_id__in=member_ids)
        return qs.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsLeadership()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
