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

        stats = {}

        # Total members in scope
        stats['total_members'] = member_ids.count() if hasattr(member_ids, 'count') else len(member_ids)

        # Today's prayer completion
        from prayers.models import PrayerLog
        prayer_qs = PrayerLog.objects.filter(member_id__in=member_ids, date=today)
        total_prayers = prayer_qs.count()
        completed_prayers = prayer_qs.filter(status='completed').count()
        stats['prayer_completion_today'] = {
            'total': total_prayers,
            'completed': completed_prayers,
            'rate': round(completed_prayers / total_prayers * 100, 1) if total_prayers > 0 else 0,
        }

        # Latest Friday attendance
        from friday_attendance.models import FridayMeetingSession, FridayAttendanceRecord
        latest_session = FridayMeetingSession.objects.order_by('-date').first()
        if latest_session:
            att_qs = FridayAttendanceRecord.objects.filter(
                session=latest_session, member_id__in=member_ids
            )
            stats['latest_friday'] = {
                'date': str(latest_session.date),
                'present': att_qs.filter(status='present').count(),
                'absent': att_qs.filter(status='absent').count(),
                'total': att_qs.count(),
            }

        # Pending follow-ups
        from followups.models import FollowUpRecord
        stats['pending_followups'] = FollowUpRecord.objects.filter(
            member_id__in=member_ids, status='pending'
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
