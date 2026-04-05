import uuid
from django.db import models
from django.conf import settings


class FollowUpRecord(models.Model):
    """Tracks follow-up interactions between servants and members."""

    class FollowUpType(models.TextChoices):
        PHONE_CALL = 'phone_call', 'مكالمة هاتفية'
        VISIT = 'visit', 'زيارة'
        CHAT_MESSAGE = 'chat_message', 'رسالة'
        MEETING = 'meeting', 'اجتماع'
        OTHER = 'other', 'أخرى'

    class Priority(models.TextChoices):
        LOW = 'low', 'منخفضة'
        MEDIUM = 'medium', 'متوسطة'
        HIGH = 'high', 'عالية'
        URGENT = 'urgent', 'عاجلة'

    class Status(models.TextChoices):
        COMPLETED = 'completed', 'مكتملة'
        PENDING = 'pending', 'معلقة'
        OVERDUE = 'overdue', 'متأخرة'
        CANCELLED = 'cancelled', 'ملغاة'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='followup_records', verbose_name='المخدوم',
    )
    servant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='followups_made', verbose_name='الخادم',
    )
    type = models.CharField('النوع', max_length=20, choices=FollowUpType.choices)
    date = models.DateTimeField('التاريخ والوقت')
    summary = models.TextField('ملخص')
    outcome = models.TextField('النتيجة', blank=True, null=True)
    priority = models.CharField(
        'الأولوية', max_length=10,
        choices=Priority.choices, default=Priority.MEDIUM,
    )
    status = models.CharField(
        'الحالة', max_length=15,
        choices=Status.choices, default=Status.PENDING,
    )
    next_followup_date = models.DateField('تاريخ المتابعة القادمة', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_followups', verbose_name='أنشأه',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سجل متابعة'
        verbose_name_plural = 'سجلات المتابعة'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['servant', 'status']),
            models.Index(fields=['next_followup_date']),
        ]

    def __str__(self):
        return f'{self.get_type_display()} - {self.member} - {self.date.date()}'
