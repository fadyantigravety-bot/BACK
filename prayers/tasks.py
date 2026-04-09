from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta


@shared_task
def create_daily_prayer_logs():
    """Create prayer logs for all active members for today."""
    from .models import PrayerDefinition, PrayerLog
    from accounts.models import User
    from notifications.services import send_bulk_push
    from notifications.models import Notification

    today = timezone.localdate()
    active_prayers = PrayerDefinition.objects.filter(is_active=True)
    members = User.objects.filter(role='member', is_active=True)

    created_count = 0
    notified_members = []
    
    for member in members:
        has_new = False
        for prayer in active_prayers:
            scheduled_dt = timezone.make_aware(
                datetime.combine(today,  prayer.scheduled_time)
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
                has_new = True
                
        if has_new:
            notified_members.append(member)

    if notified_members:
        send_bulk_push(
            users=notified_members,
            title="صلوات اليوم ✝️",
            body="تمت إضافة صلوات اليوم في سجلاتك. لا تنس تحديدها بعد الانتهاء منها.",
            notification_type=Notification.NotificationType.PRAYER_ALERT,
        )

    return f'Created {created_count} prayer logs for {today} and notified {len(notified_members)} members'
