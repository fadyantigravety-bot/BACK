from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from core.permissions import IsPriestOrServiceLeader
from core.scoping import get_scoped_member_users


class DashboardStatsView(APIView):
    """Aggregated dashboard statistics scoped by role."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        member_ids = get_scoped_member_users(user)
        today = timezone.localdate()
        period = request.query_params.get('period', 'today') # today, week, month
        
        # Calculate start and end dates based on period
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = today.replace(day=1)
            next_month = start_date.replace(month=start_date.month % 12 + 1, year=start_date.year + (start_date.month // 12))
            end_date = next_month - timedelta(days=1)
        else: # today
            start_date = today
            end_date = today

        stats = {}

        # Total members in scope
        stats['total_members'] = member_ids.count() if hasattr(member_ids, 'count') else len(member_ids)

        # Prayer completion for period
        from prayers.models import PrayerLog
        prayer_qs = PrayerLog.objects.filter(member_id__in=member_ids, date__range=[start_date, end_date])
        total_prayers = prayer_qs.count()
        completed_prayers = prayer_qs.filter(status='completed').count()
        stats['prayer_completion'] = {
            'total': total_prayers,
            'completed': completed_prayers,
            'rate': round(completed_prayers / total_prayers * 100, 1) if total_prayers > 0 else 0,
        }

        # Friday attendance (latest or all in period? Let's do all sessions in period)
        from friday_attendance.models import FridayMeetingSession, FridayAttendanceRecord
        sessions_in_period = FridayMeetingSession.objects.filter(date__range=[start_date, end_date])
        
        # If no sessions in period, fallback to latest
        if not sessions_in_period.exists() and period == 'today':
           sessions_in_period = FridayMeetingSession.objects.order_by('-date')[:1]

        if sessions_in_period.exists():
            att_qs = FridayAttendanceRecord.objects.filter(
                session__in=sessions_in_period, member_id__in=member_ids
            )
            stats['friday'] = {
                'title': 'حضور الجمعة' if period != 'today' else f"حضور آخر جمعة ({sessions_in_period.first().date})",
                'present': att_qs.filter(status='present').count(),
                'absent': att_qs.filter(status='absent').count(),
                'total': att_qs.count(),
            }

        # Pending follow-ups
        from followups.models import FollowUpRecord
        stats['pending_followups'] = FollowUpRecord.objects.filter(
            member_id__in=member_ids, status='pending', date__range=[start_date, end_date]
        ).count()
        stats['overdue_followups'] = FollowUpRecord.objects.filter(
            member_id__in=member_ids, status='overdue'
        ).count()

        # Confession stats (priest only)
        if user.role == 'priest':
            from confessions.models import ConfessionRecord
            stats['confession'] = {
                'overdue': ConfessionRecord.objects.filter(is_overdue=True).count(),
                'confessed': ConfessionRecord.objects.filter(has_confessed=True).count(),
            }

        # Unread messages
        from messaging.models import ConversationParticipant, Message
        participations = ConversationParticipant.objects.filter(user=user)
        unread = 0
        for p in participations:
            if p.last_read_at:
                unread += Message.objects.filter(
                    conversation=p.conversation, created_at__gt=p.last_read_at
                ).exclude(sender=user).count()
            else:
                unread += Message.objects.filter(
                    conversation=p.conversation
                ).exclude(sender=user).count()
        stats['unread_messages'] = unread

        # Birthdays today
        from accounts.models import MemberProfile
        stats['birthdays_today'] = MemberProfile.objects.filter(
            user_id__in=member_ids,
            date_of_birth__month=today.month,
            date_of_birth__day=today.day,
        ).count()

        return Response(stats)


class BirthdayListView(APIView):
    """List birthdays for a given period."""
    permission_classes = [IsPriestOrServiceLeader]

    def get(self, request):
        from accounts.models import MemberProfile
        member_ids = get_scoped_member_users(request.user)
        today = timezone.localdate()
        period = request.query_params.get('period', 'week')

        qs = MemberProfile.objects.filter(user_id__in=member_ids)

        if period == 'today':
            qs = qs.filter(date_of_birth__month=today.month, date_of_birth__day=today.day)
        elif period == 'week':
            end = today + timedelta(days=7)
            # Filter by month/day range
            qs = qs.filter(
                Q(date_of_birth__month=today.month, date_of_birth__day__gte=today.day) |
                Q(date_of_birth__month=end.month, date_of_birth__day__lte=end.day)
            )
        elif period == 'month':
            qs = qs.filter(date_of_birth__month=today.month)

        data = qs.values(
            'user__id', 'user__first_name', 'user__last_name',
            'date_of_birth', 'service_group__name',
        )
        return Response(list(data))
