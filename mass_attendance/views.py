from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsLeadership
from core.scoping import get_scoped_member_users
from .models import MassAttendanceRecord
from .serializers import MassAttendanceRecordSerializer


class MassAttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MassAttendanceRecordSerializer
    filterset_fields = ['member', 'date', 'attended']
    ordering_fields = ['date']

    def get_queryset(self):
        user = self.request.user
        qs = MassAttendanceRecord.objects.select_related('member', 'recorded_by')
        if user.role == 'priest':
            return qs
        if user.role == 'member':
            return qs.filter(member=user)
        member_ids = get_scoped_member_users(user)
        return qs.filter(member_id__in=member_ids)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
