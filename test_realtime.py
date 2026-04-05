import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from notifications.services import create_notification
from accounts.models import User

# Define the test message
title = "تنبيه هام للجميع 📢"
body = "أهلاً بك! هذا الإشعار لاختبار الـ Real-Time وصوت الإشعارات داخل التطبيق."

print("Sending Real-time WebSockets test to all users...")
users = User.objects.all()

for user in users:
    create_notification(
        recipient=user,
        title=title,
        body=body,
        notification_type='system',
        send_push=False
    )
print(f"✅ Successfully sent real-time notification to {users.count()} users.")
