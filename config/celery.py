import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('koinonia')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # --- Prayer Tasks ---
    # Runs daily at 12:01 AM
    'create-daily-prayer-logs': {
        'task': 'prayers.tasks.create_daily_prayer_logs',
        'schedule': crontab(hour=0, minute=1),
    },

    # --- Confession Tasks ---
    # Saturday at 10:00 AM and 5:00 PM
    'saturday_confession_10am': {
        'task': 'confessions.tasks.create_weekend_confession_records',
        'schedule': crontab(hour=10, minute=0, day_of_week='sat'),
    },
    'saturday_confession_5pm': {
        'task': 'confessions.tasks.create_weekend_confession_records',
        'schedule': crontab(hour=17, minute=0, day_of_week='sat'),
    },
    # Sunday at 10:00 AM and 5:00 PM
    'sunday_confession_10am': {
        'task': 'confessions.tasks.create_weekend_confession_records',
        'schedule': crontab(hour=10, minute=0, day_of_week='sun'),
    },
    'sunday_confession_5pm': {
        'task': 'confessions.tasks.create_weekend_confession_records',
        'schedule': crontab(hour=17, minute=0, day_of_week='sun'),
    },

    # --- Existing Tasks ---
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
