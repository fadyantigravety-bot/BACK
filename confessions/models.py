import uuid
from django.db import models
from django.conf import settings


class ConfessionRecord(models.Model):
    """Administrative confession follow-up status.
    NEVER stores private confession content — only tracking data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='confession_records', verbose_name='المخدوم',
    )
    has_confessed = models.BooleanField('اعترف', default=False)
    last_confession_date = models.DateField('تاريخ آخر اعتراف', blank=True, null=True)
    follow_up_note = models.TextField(
        'ملاحظة المتابعة', blank=True, null=True,
        help_text='ملاحظة إدارية فقط - لا تخزّن محتوى الاعتراف أبداً',
    )
    is_overdue = models.BooleanField('متأخر', default=False)
    overdue_threshold_days = models.IntegerField('حد التأخر (أيام)', default=30)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='recorded_confessions', verbose_name='سُجل بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سجل اعتراف'
        verbose_name_plural = 'سجلات الاعتراف'
        ordering = ['-updated_at']

    def __str__(self):
        status = 'اعترف' if self.has_confessed else 'لم يعترف'
        return f'{self.member} - {status}'
