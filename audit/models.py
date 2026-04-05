import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Tracks important actions for accountability and security."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='audit_logs', verbose_name='المستخدم',
    )
    action = models.CharField('الإجراء', max_length=100)
    target_type = models.CharField('نوع الهدف', max_length=100)
    target_id = models.UUIDField('معرف الهدف')
    details = models.JSONField('التفاصيل', blank=True, null=True)
    ip_address = models.GenericIPAddressField('عنوان IP', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'سجل مراجعة'
        verbose_name_plural = 'سجلات المراجعة'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.action} - {self.created_at}'
