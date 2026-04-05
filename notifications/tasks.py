from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def check_birthday_reminders():
    """Send birthday notifications for today's birthdays."""
    from accounts.models import MemberProfile, User
    from .services import create_notification

    today = timezone.localdate()
    birthday_members = MemberProfile.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day,
        is_active_member=True,
    ).select_related('user', 'assigned_servant')

    count = 0
    for member in birthday_members:
        # Notify assigned servant
        if member.assigned_servant:
            create_notification(
                recipient=member.assigned_servant,
                title='🎂 عيد ميلاد',
                body=f'اليوم عيد ميلاد {member.user.full_name}',
                notification_type='birthday',
                reference_type='MemberProfile',
                reference_id=member.id,
            )
            count += 1

        # Notify priests
        priests = User.objects.filter(role='priest', is_active=True)
        for priest in priests:
            create_notification(
                recipient=priest,
                title='🎂 عيد ميلاد',
                body=f'اليوم عيد ميلاد {member.user.full_name}',
                notification_type='birthday',
                reference_type='MemberProfile',
                reference_id=member.id,
            )
            count += 1

    return f'Sent {count} birthday notifications'


@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 90 days."""
    from .models import Notification
    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    return f'Deleted {deleted} old notifications'
