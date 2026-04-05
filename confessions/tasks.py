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
