import uuid
from django.db import models
from django.conf import settings


class FridayMeetingSession(models.Model):
    """Represents a single Friday meeting session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField('تاريخ الجمعة', unique=True)
    title = models.CharField('العنوان', max_length=200, blank=True, null=True)
    service_stage = models.ForeignKey(
        'church.ServiceStage', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='المرحلة',
        help_text='اتركه فارغاً لجميع المراحل',
    )
    notes = models.TextField('ملاحظات', blank=True, null=True)
    is_locked = models.BooleanField('مغلق', default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='أنشأه',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'جلسة اجتماع الجمعة'
        verbose_name_plural = 'جلسات اجتماع الجمعة'
        ordering = ['-date']

    def __str__(self):
        return f'اجتماع الجمعة - {self.date}'


class FridayAttendanceRecord(models.Model):
    """Individual attendance record for a member at a Friday session."""

    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', 'حاضر'
        ABSENT = 'absent', 'غائب'
        EXCUSED = 'excused', 'معتذر'
        LATE = 'late', 'متأخر'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        FridayMeetingSession, on_delete=models.CASCADE,
        related_name='attendance_records', verbose_name='الجلسة',
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='friday_attendance_records', verbose_name='المخدوم',
    )
    status = models.CharField(
        'الحالة', max_length=10,
        choices=AttendanceStatus.choices, default=AttendanceStatus.ABSENT,
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='marked_friday_records', verbose_name='سُجل بواسطة',
    )
    absence_reason = models.TextField('سبب الغياب', blank=True, null=True)
    notes = models.TextField('ملاحظات', blank=True, null=True)
    marked_at = models.DateTimeField('وقت التسجيل', auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سجل حضور الجمعة'
        verbose_name_plural = 'سجلات حضور الجمعة'
        unique_together = ('session', 'member')
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['session', 'status']),
        ]

    def __str__(self):
        return f'{self.member} - {self.session.date} - {self.get_status_display()}'
