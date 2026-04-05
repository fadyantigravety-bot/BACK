import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with phone-based auth and role system."""

    class Role(models.TextChoices):
        PRIEST = 'priest', 'كاهن'
        SERVICE_LEADER = 'service_leader', 'مسؤول خدمة'
        SERVANT = 'servant', 'خادم'
        MEMBER = 'member', 'مخدوم'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField('رقم الهاتف', max_length=20, unique=True, db_index=True)
    email = models.EmailField('البريد الإلكتروني', blank=True, null=True)
    first_name = models.CharField('الاسم الأول', max_length=100)
    last_name = models.CharField('اسم العائلة', max_length=100)
    role = models.CharField('الدور', max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField('نشط', default=True)
    is_staff = models.BooleanField('طاقم الإدارة', default=False)
    fcm_token = models.TextField('FCM Token', blank=True, null=True)
    device_type = models.CharField(
        max_length=10,
        choices=[('android', 'Android'), ('ios', 'iOS')],
        blank=True, null=True,
    )
    notifications_enabled = models.BooleanField('الإشعارات مفعلة', default=True)
    language = models.CharField('اللغة', max_length=10, default='ar')
    avatar = models.ImageField('الصورة الشخصية', upload_to='avatars/', blank=True, null=True)
    date_joined = models.DateTimeField('تاريخ الانضمام', auto_now_add=True)
    last_login = models.DateTimeField('آخر تسجيل دخول', blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class PriestProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='priest_profile')
    ordination_date = models.DateField('تاريخ الرسامة', blank=True, null=True)
    can_manage_confessions = models.BooleanField('إدارة الاعتراف', default=True)
    notes = models.TextField('ملاحظات', blank=True, null=True)

    class Meta:
        verbose_name = 'ملف الكاهن'
        verbose_name_plural = 'ملفات الكهنة'

    def __str__(self):
        return f'كاهن: {self.user.full_name}'


class ServiceLeaderProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='serviceleaderprofile')
    service_stage = models.ForeignKey(
        'church.ServiceStage', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='مرحلة الخدمة',
    )
    can_view_confession_status = models.BooleanField('عرض حالة الاعتراف', default=False)
    appointed_date = models.DateField('تاريخ التعيين', blank=True, null=True)
    notes = models.TextField('ملاحظات', blank=True, null=True)

    class Meta:
        verbose_name = 'ملف مسؤول الخدمة'
        verbose_name_plural = 'ملفات مسؤولي الخدمة'

    def __str__(self):
        return f'مسؤول: {self.user.full_name}'


class ServantProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='servant_profile')
    service_group = models.ForeignKey(
        'church.ServiceGroup', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='مجموعة الخدمة',
    )
    supervisor = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='supervised_servants',
        verbose_name='المشرف',
    )
    can_view_prayer_data = models.BooleanField('عرض بيانات الصلاة', default=False)
    can_view_mass_data = models.BooleanField('عرض بيانات القداس', default=False)
    joined_service_date = models.DateField('تاريخ بدء الخدمة', blank=True, null=True)
    notes = models.TextField('ملاحظات', blank=True, null=True)

    class Meta:
        verbose_name = 'ملف الخادم'
        verbose_name_plural = 'ملفات الخدام'

    def __str__(self):
        return f'خادم: {self.user.full_name}'


class MemberProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', 'ذكر'
        FEMALE = 'female', 'أنثى'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    date_of_birth = models.DateField('تاريخ الميلاد')
    gender = models.CharField('الجنس', max_length=10, choices=Gender.choices)
    address = models.TextField('العنوان', blank=True, null=True)
    guardian_name = models.CharField('اسم ولي الأمر', max_length=200, blank=True, null=True)
    guardian_phone = models.CharField('هاتف ولي الأمر', max_length=20, blank=True, null=True)
    baptism_date = models.DateField('تاريخ المعمودية', blank=True, null=True)
    service_group = models.ForeignKey(
        'church.ServiceGroup', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='members',
        verbose_name='مجموعة الخدمة',
    )
    assigned_servant = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_members',
        verbose_name='الخادم المسؤول',
    )
    is_active_member = models.BooleanField('عضو نشط', default=True)
    join_date = models.DateField('تاريخ الانضمام', auto_now_add=True)
    notes = models.TextField('ملاحظات', blank=True, null=True)

    class Meta:
        verbose_name = 'ملف المخدوم'
        verbose_name_plural = 'ملفات المخدومين'
        ordering = ['user__first_name']

    def __str__(self):
        return f'مخدوم: {self.user.full_name}'
