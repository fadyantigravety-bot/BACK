from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Exists, OuterRef
from django.contrib.auth import get_user_model
from core.permissions import IsPriest
from .models import ConfessionRecord, ConfessionAttendance
from .serializers import ConfessionRecordSerializer, DailyConfessionAttendanceSerializer
from audit.services import log_action
import datetime

User = get_user_model()


class ConfessionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ConfessionRecordSerializer
    filterset_fields = ['member', 'has_confessed', 'is_overdue']
    search_fields = ['member__first_name', 'member__last_name']

    def get_queryset(self):
        user = self.request.user
        qs = ConfessionRecord.objects.select_related('member').annotate(
            total_confessions=Count('member__confession_attendances', filter=Q(member__confession_attendances__attended=True))
        )
        if user.role == 'priest':
            return qs.all()
        if user.role == 'service_leader':
            try:
                if user.serviceleaderprofile.can_view_confession_status:
                    from core.scoping import get_scoped_member_users
                    member_ids = get_scoped_member_users(user)
                    return qs.filter(member_id__in=member_ids)
            except Exception:
                pass
        return qs.none()

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


class DailyConfessionListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        qs = User.objects.filter(role='member')
        
        # Scoping based on role limit
        if user.role == 'member':
            qs = qs.filter(id=user.id)
        elif user.role == 'service_leader':
            try:
                if user.serviceleaderprofile.can_view_confession_status:
                    from core.scoping import get_scoped_member_users
                    member_ids = get_scoped_member_users(user)
                    qs = qs.filter(id__in=member_ids)
                else:
                    qs = qs.none()
            except Exception:
                qs = qs.none()
        elif user.role not in ['priest', 'superadmin']:
            qs = qs.none()

        target_weekday = target_date.weekday()
        days_since_saturday = (target_weekday + 2) % 7
        week_start = target_date - datetime.timedelta(days=days_since_saturday)
        week_end = week_start + datetime.timedelta(days=6)

        attended_subquery = ConfessionAttendance.objects.filter(
            member=OuterRef('pk'), date__range=[week_start, week_end], attended=True
        )

        qs = qs.annotate(
            total_confessions=Count('confession_attendances', filter=Q(confession_attendances__attended=True)),
            attended=Exists(attended_subquery)
        ).order_by('first_name', 'last_name')

        serializer = DailyConfessionAttendanceSerializer(qs, many=True)
        return Response(serializer.data)


class MarkConfessionAttendanceView(views.APIView):
    permission_classes = [IsPriest]

    def post(self, request):
        member_id = request.data.get('member_id')
        date_str = request.data.get('date')
        
        if not member_id or not date_str:
            return Response({"error": "member_id and date are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
        target_weekday = target_date.weekday()
        days_since_saturday = (target_weekday + 2) % 7
        week_start = target_date - datetime.timedelta(days=days_since_saturday)
        week_end = week_start + datetime.timedelta(days=6)

        # Check if any attendance exists for this week
        existing = ConfessionAttendance.objects.filter(
            member_id=member_id, date__range=[week_start, week_end], attended=True
        ).exists()

        if not existing:
            attendance, _ = ConfessionAttendance.objects.get_or_create(
                member_id=member_id, date=target_date, defaults={'recorded_by': request.user}
            )
            if not attendance.attended:
                attendance.attended = True
                attendance.recorded_by = request.user
                attendance.save()
                
                # Update legacy profile tracker
                ConfessionRecord.objects.update_or_create(
                    member_id=member_id,
                    defaults={
                        'has_confessed': True,
                        'last_confession_date': target_date,
                        'is_overdue': False,
                        'recorded_by': request.user
                    }
                )

                log_action(request.user, 'daily_confession_marked', 'ConfessionAttendance',
                           attendance.id, {'member_id': str(member_id), 'date': date_str})
                       
        return Response({"status": "success"})

