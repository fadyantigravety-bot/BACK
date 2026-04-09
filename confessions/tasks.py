from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def check_overdue_confessions():
    """Flag members whose last confession exceeds the threshold."""
    from .models import ConfessionRecord
    from django.conf import settings

    threshold = settings.CONFESSION_OVERDUE_DAYS
    cutoff = timezone.localdate() - timedelta(days=threshold)

    updated = ConfessionRecord.objects.filter(
        last_confession_date__lt=cutoff,
        is_overdue=False,
    ).update(is_overdue=True)

    # Also flag members who never confessed
    never = ConfessionRecord.objects.filter(
        last_confession_date__isnull=True,
        has_confessed=False,
        is_overdue=False,
    ).update(is_overdue=True)

    return f'Marked {updated + never} confession records as overdue'


@shared_task
def create_weekend_confession_records():
    """Create ConfessionAttendance records for today and send notifications."""
    from .models import ConfessionAttendance
    from accounts.models import User
    from notifications.services import send_bulk_push
    from notifications.models import Notification

    today = timezone.localdate()
    members = User.objects.filter(role='member', is_active=True)

    created_count = 0
    notified_members = []

    for member in members:
        _, created = ConfessionAttendance.objects.get_or_create(
            member=member,
            date=today,
            defaults={
                'attended': False,
            }
        )
        if created:
            created_count += 1
            notified_members.append(member)

    if notified_members:
        send_bulk_push(
            users=notified_members,
            title="تذكير بالاعتراف ⛪",
            body="يوجد اعترافات اليوم في الكنيسة، لا تفوت الفرصة للتوبة والاعتراف.",
            notification_type=Notification.NotificationType.ANNOUNCEMENT,
        )

    return f'Created {created_count} confession records for {today} and notified {len(notified_members)} members'
