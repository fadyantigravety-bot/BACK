from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'is_pushed', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_pushed')
    search_fields = ('title', 'body', 'recipient__first_name')
