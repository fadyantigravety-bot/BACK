from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta


@shared_task
def create_daily_prayer_logs():
    """Create prayer logs for all active members for today."""
    from .models import PrayerDefinition, PrayerLog
    from accounts.models import User

    today = timezone.localdate()
    active_prayers = PrayerDefinition.objects.filter(is_active=True)
    members = User.objects.filter(role='member', is_active=True)

    created_count = 0
    for member in members:
        for prayer in active_prayers:
            scheduled_dt = timezone.make_aware(
                datetime.combine(today, prayer.scheduled_time)
            )
            _, created = PrayerLog.objects.get_or_create(
                member=member,
                prayer=prayer,
                date=today,
                defaults={
                    'status': 'pending',
                    'scheduled_time': scheduled_dt,
                },
            )
            if created:
                created_count += 1

    return f'Created {created_count} prayer logs for {today}'
