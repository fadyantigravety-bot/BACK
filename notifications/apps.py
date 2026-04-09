import sys
import threading
from django.apps import AppConfig


def send_startup_test_push():
    from accounts.models import User
    from notifications.services import send_bulk_push
    from notifications.models import Notification
    
    # Send to staff/admin users, or the first user if no staff exists
    users = list(User.objects.filter(is_staff=True))
    if not users:
        first_user = User.objects.first()
        if first_user:
            users = [first_user]

    if users:
        send_bulk_push(
            users=users,
            title="تجربة الإشعارات 🚀",
            body="السيرفر يعمل الآن ونظام الإشعارات متصل بنجاح!",
            notification_type=Notification.NotificationType.SYSTEM,
        )


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'الإشعارات'

    def ready(self):
        # Run only on server spin up (runserver or daphne/gunicorn in production)
        is_server = False
        allowed_commands = ['runserver', 'daphne', 'gunicorn']
        for arg in sys.argv:
            if any(cmd in arg for cmd in allowed_commands):
                is_server = True
                break
        
        if is_server:
            # We wait 5 seconds after ready() to avoid blocking server start
            threading.Timer(5.0, send_startup_test_push).start()
