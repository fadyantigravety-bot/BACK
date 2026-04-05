import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('koinonia')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat schedule
app.conf.beat_schedule = {
    'create-daily-prayer-logs': {
        'task': 'prayers.tasks.create_daily_prayer_logs',
        'schedule': crontab(hour=0, minute=0),
    },
    'check-birthday-reminders': {
        'task': 'notifications.tasks.check_birthday_reminders',
        'schedule': crontab(hour=7, minute=0),
    },
    'check-overdue-confessions': {
        'task': 'confessions.tasks.check_overdue_confessions',
        'schedule': crontab(hour=8, minute=0),
    },
    'check-overdue-followups': {
        'task': 'followups.tasks.check_overdue_followups',
        'schedule': crontab(hour=9, minute=0),
    },
    'compute-weekly-attendance-stats': {
        'task': 'friday_attendance.tasks.compute_weekly_stats',
        'schedule': crontab(hour=2, minute=0, day_of_week='saturday'),
    },
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=3, minute=0, day_of_week='sunday'),
    },
}
