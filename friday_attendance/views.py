from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from core.permissions import IsLeadership, IsPriestOrServiceLeader
from core.scoping import get_scoped_members, get_scoped_member_users
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
            return [IsLeadership()]
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
        
        # Role scoping
        if user.role not in ('priest',):
            member_ids = get_scoped_member_users(user)
            qs = qs.filter(member_id__in=member_ids)
            
        # Period filtering
        period = self.request.query_params.get('period')
        if period:
            today = timezone.localdate()
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == 'month':
                start_date = today.replace(day=1)
                if start_date.month == 12:
                    next_month = start_date.replace(year=start_date.year + 1, month=1)
                else:
                    next_month = start_date.replace(month=start_date.month + 1)
                end_date = next_month - timedelta(days=1)
            else: # today
                start_date = today
                end_date = today
            
            qs = qs.filter(session__date__range=[start_date, end_date])
            
        return qs

    def list(self, request, *args, **kwargs):
        status_filter = request.query_params.get('status')
        include_missing = request.query_params.get('include_missing', 'false').lower() == 'true'
        
        # Special logic for absentees report
        if status_filter == 'absent' and include_missing:
            user = request.user
            period = request.query_params.get('period', 'today')
            
            # Determine date range
            today = timezone.localdate()
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == 'month':
                start_date = today.replace(day=1)
                if start_date.month == 12:
                    next_month = start_date.replace(year=start_date.year + 1, month=1)
                else:
                    next_month = start_date.replace(month=start_date.month + 1)
                end_date = next_month - timedelta(days=1)
            else: # today
                start_date = today
                end_date = today

            # Get latest session if no sessions in range
            sessions = FridayMeetingSession.objects.filter(date__range=[start_date, end_date])
            if not sessions.exists() and period == 'today':
                sessions = FridayMeetingSession.objects.order_by('-date')[:1]
            
            if not sessions.exists():
                return Response([])

            session = sessions.first() # Base the "missing" on the latest session in range
            
            # 1. Get all members in scope
            all_members_qs = get_scoped_members(user).select_related('user')
            
            # 2. Get members with 'present' or 'late' or 'excused' records
            present_member_ids = FridayAttendanceRecord.objects.filter(
                session__in=sessions,
                status__in=['present', 'late', 'excused']
            ).values_list('member_id', flat=True)
            
            # 3. Members who are NOT in the present list are "Absent"
            absent_members = all_members_qs.exclude(user_id__in=present_member_ids)
            
            # 4. Format the output to match what the frontend expects
            results = []
            for member in absent_members:
                # Check if there's an explicit 'absent' record for the reason
                explicit_record = FridayAttendanceRecord.objects.filter(
                    session=session, member=member.user, status='absent'
                ).first()
                
                results.append({
                    'id': explicit_record.id if explicit_record else None,
                    'member': member.user.id,
                    'member_name': f"{member.user.first_name} {member.user.last_name}",
                    'status': 'absent',
                    'session_date': session.date.isoformat(),
                    'absence_reason': explicit_record.absence_reason if explicit_record else "لم يسجل حضور",
                    'notes': explicit_record.notes if explicit_record else ""
                })
            
            return Response(results)

        return super().list(request, *args, **kwargs)

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
