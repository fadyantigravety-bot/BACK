from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from core.permissions import IsLeadership, IsPriestOrServiceLeader
from core.scoping import get_scoped_member_users
from .models import FridayMeetingSession, FridayAttendanceRecord
from .serializers import (
    FridayMeetingSessionSerializer, FridayAttendanceRecordSerializer,
    BulkAttendanceSerializer,
)


class FridayMeetingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = FridayMeetingSessionSerializer
    filterset_fields = ['service_stage', 'is_locked', 'date']
    ordering_fields = ['date']

    def get_queryset(self):
        return FridayMeetingSession.objects.annotate(
            total_present=Count('attendance_records', filter=Q(attendance_records__status='present')),
            total_absent=Count('attendance_records', filter=Q(attendance_records__status='absent')),
            total_excused=Count('attendance_records', filter=Q(attendance_records__status='excused')),
        )

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPriestOrServiceLeader()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FridayAttendanceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FridayAttendanceRecordSerializer
    filterset_fields = ['session', 'member', 'status']
    search_fields = ['member__first_name', 'member__last_name']

    def get_queryset(self):
        user = self.request.user
        qs = FridayAttendanceRecord.objects.select_related('member', 'marked_by', 'session')
        if user.role in ('priest',):
            return qs
        member_ids = get_scoped_member_users(user)
        return qs.filter(member_id__in=member_ids)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsLeadership()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[IsLeadership])
    def bulk_mark(self, request):
        """Mark attendance for multiple members at once."""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data['session_id']
        records = serializer.validated_data['records']
        created = []
        for record in records:
            obj, _ = FridayAttendanceRecord.objects.update_or_create(
                session_id=session_id,
                member_id=record['member_id'],
                defaults={
                    'status': record['status'],
                    'marked_by': request.user,
                    'absence_reason': record.get('absence_reason', ''),
                },
            )
            created.append(obj)
        # WebSocket broadcast
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'attendance_{session_id}',
                {
                    'type': 'attendance.marked',
                    'data': {'session_id': str(session_id), 'count': len(created)},
                },
            )
        except Exception:
            pass
        return Response({'status': 'تم تسجيل الحضور', 'count': len(created)})

    @action(detail=False, methods=['get'])
    def consecutive_absences(self, request):
        """Get members with consecutive Friday absences."""
        min_absences = int(request.query_params.get('min', 2))
        member_ids = get_scoped_member_users(request.user)
        from django.db.models import Count
        absent_members = (
            FridayAttendanceRecord.objects
            .filter(status='absent', member_id__in=member_ids)
            .values('member', 'member__first_name', 'member__last_name')
            .annotate(absence_count=Count('id'))
            .filter(absence_count__gte=min_absences)
            .order_by('-absence_count')
        )
        return Response(list(absent_members))
