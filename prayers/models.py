import uuid
from django.db import models
from django.conf import settings


class PrayerDefinition(models.Model):
    """Admin-managed list of daily Christian prayers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('اسم الصلاة', max_length=200)
    description = models.TextField('الوصف', blank=True, null=True)
    scheduled_time = models.TimeField('وقت الصلاة')
    order = models.IntegerField('الترتيب', default=0)
    is_active = models.BooleanField('نشط', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='أنشأها',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'صلاة'
        verbose_name_plural = 'الصلوات'
        ordering = ['order', 'scheduled_time']

    def __str__(self):
        return f'{self.name} ({self.scheduled_time})'


class PrayerLog(models.Model):
    """Tracks a member's response to a specific prayer on a specific day."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'في الانتظار'
        COMPLETED = 'completed', 'تمت'
        MISSED = 'missed', 'فائتة'
        SNOOZED = 'snoozed', 'مؤجلة'
        PENDING_CONFIRMATION = 'pending_confirmation', 'في انتظار التأكيد'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='prayer_logs', verbose_name='المخدوم',
    )
    prayer = models.ForeignKey(
        PrayerDefinition, on_delete=models.CASCADE,
        related_name='logs', verbose_name='الصلاة',
    )
    date = models.DateField('التاريخ')
    status = models.CharField(
        'الحالة', max_length=25,
        choices=Status.choices, default=Status.PENDING,
    )
    scheduled_time = models.DateTimeField('الوقت المجدول')
    alert_shown_at = models.DateTimeField('وقت عرض التنبيه', blank=True, null=True)
    first_response_at = models.DateTimeField('وقت الاستجابة الأولى', blank=True, null=True)
    followup_sent_at = models.DateTimeField('وقت إرسال المتابعة', blank=True, null=True)
    final_response_at = models.DateTimeField('وقت الاستجابة النهائية', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سجل صلاة'
        verbose_name_plural = 'سجلات الصلوات'
        unique_together = ('member', 'prayer', 'date')
        indexes = [
            models.Index(fields=['member', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f'{self.member} - {self.prayer.name} - {self.date}'
