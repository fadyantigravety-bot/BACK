import uuid
from django.db import models
from django.conf import settings


class MassAttendanceRecord(models.Model):
    """Tracks whether a member attended a mass service."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='mass_attendance_records', verbose_name='المخدوم',
    )
    date = models.DateField('التاريخ')
    attended = models.BooleanField('حضر', default=False)
    church_name = models.CharField('اسم الكنيسة', max_length=200, blank=True, null=True)
    mass_type = models.CharField(
        'نوع القداس', max_length=100, blank=True, null=True,
        help_text='مثال: قداس أحد، قداس عيد',
    )
    notes = models.TextField('ملاحظات', blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='recorded_mass_records', verbose_name='سُجل بواسطة',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'سجل حضور القداس'
        verbose_name_plural = 'سجلات حضور القداس'
        indexes = [
            models.Index(fields=['member', 'date']),
        ]
        ordering = ['-date']

    def __str__(self):
        status = 'حضر' if self.attended else 'لم يحضر'
        return f'{self.member} - {self.date} - {status}'
