import uuid
from django.db import models
from django.conf import settings


class ServiceStage(models.Model):
    """Service stage (e.g. إعدادي, ثانوي, جامعيين)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('اسم المرحلة', max_length=200)
    description = models.TextField('الوصف', blank=True, null=True)
    order = models.IntegerField('الترتيب', default=0)
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)

    class Meta:
        verbose_name = 'مرحلة خدمة'
        verbose_name_plural = 'مراحل الخدمة'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ServiceGroup(models.Model):
    """A group within a service stage (e.g. مجموعة أ)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('اسم المجموعة', max_length=200)
    stage = models.ForeignKey(
        ServiceStage, on_delete=models.CASCADE,
        related_name='groups', verbose_name='المرحلة',
    )
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='led_groups',
        verbose_name='قائد المجموعة',
    )
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)

    class Meta:
        verbose_name = 'مجموعة خدمة'
        verbose_name_plural = 'مجموعات الخدمة'
        ordering = ['stage__order', 'name']

    def __str__(self):
        return f'{self.stage.name} - {self.name}'
