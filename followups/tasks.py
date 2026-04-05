from celery import shared_task
from django.utils import timezone


@shared_task
def check_overdue_followups():
    """Flag follow-ups past their next_followup_date."""
    from .models import FollowUpRecord
    from notifications.services import create_notification

    today = timezone.localdate()
    overdue_records = FollowUpRecord.objects.filter(
        status='pending',
        next_followup_date__lt=today,
    )

    count = 0
    for record in overdue_records:
        record.status = 'overdue'
        record.save(update_fields=['status'])
        # Notify the servant
        create_notification(
            recipient=record.servant,
            title='متابعة متأخرة',
            body=f'المتابعة مع {record.member.full_name} متأخرة',
            notification_type='followup_due',
            reference_type='FollowUpRecord',
            reference_id=record.id,
        )
        count += 1

    return f'Marked {count} follow-ups as overdue'
