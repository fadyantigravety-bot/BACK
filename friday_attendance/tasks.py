from celery import shared_task
from django.utils import timezone


@shared_task
def compute_weekly_stats():
    """Compute weekly Friday attendance statistics."""
    from .models import FridayMeetingSession, FridayAttendanceRecord
    from django.db.models import Count, Q

    # Get last Friday's session
    today = timezone.localdate()
    last_friday = today - timezone.timedelta(days=(today.weekday() + 3) % 7)
    try:
        session = FridayMeetingSession.objects.get(date=last_friday)
    except FridayMeetingSession.DoesNotExist:
        return 'No Friday session found'

    stats = FridayAttendanceRecord.objects.filter(session=session).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        excused=Count('id', filter=Q(status='excused')),
        late=Count('id', filter=Q(status='late')),
    )

    return f'Friday {last_friday} stats: {stats}'
