import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """In-app notification record with optional push delivery."""

    class NotificationType(models.TextChoices):
        PRAYER_ALERT = 'prayer_alert', 'تنبيه صلاة'
        PRAYER_FOLLOWUP = 'prayer_followup', 'متابعة صلاة'
        ATTENDANCE_REMINDER = 'attendance_reminder', 'تذكير حضور'
        BIRTHDAY = 'birthday', 'عيد ميلاد'
        FOLLOWUP_DUE = 'followup_due', 'متابعة مطلوبة'
        MESSAGE = 'message', 'رسالة'
        ANNOUNCEMENT = 'announcement', 'إعلان'
        CONFESSION_OVERDUE = 'confession_overdue', 'تأخر اعتراف'
        ABSENCE_ALERT = 'absence_alert', 'تنبيه غياب'
        SYSTEM = 'system', 'نظام'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications', verbose_name='المستلم',
        db_index=True,
    )
    title = models.CharField('العنوان', max_length=300)
    body = models.TextField('المحتوى')
    notification_type = models.CharField(
        'النوع', max_length=25, choices=NotificationType.choices,
    )
    reference_type = models.CharField(
        'نوع المرجع', max_length=100, blank=True, null=True,
    )
    reference_id = models.UUIDField('معرف المرجع', blank=True, null=True)
    is_read = models.BooleanField('مقروء', default=False)
    is_pushed = models.BooleanField('تم الإرسال', default=False)
    scheduled_for = models.DateTimeField('مجدول لـ', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'notification_type']),
            models.Index(fields=['scheduled_for']),
        ]

    def __str__(self):
        return f'{self.title} → {self.recipient}'
