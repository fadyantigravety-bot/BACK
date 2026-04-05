from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PriestProfile, ServiceLeaderProfile, ServantProfile, MemberProfile


class PriestProfileInline(admin.StackedInline):
    model = PriestProfile
    can_delete = False


class ServiceLeaderProfileInline(admin.StackedInline):
    model = ServiceLeaderProfile
    can_delete = False


class ServantProfileInline(admin.StackedInline):
    model = ServantProfile
    can_delete = False


class MemberProfileInline(admin.StackedInline):
    model = MemberProfile
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('المعلومات الشخصية', {'fields': ('first_name', 'last_name', 'email', 'avatar')}),
        ('الدور والصلاحيات', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('الإشعارات', {'fields': ('fcm_token', 'device_type', 'notifications_enabled')}),
        ('التواريخ', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        role_inlines = {
            'priest': [PriestProfileInline],
            'service_leader': [ServiceLeaderProfileInline],
            'servant': [ServantProfileInline],
            'member': [MemberProfileInline],
        }
        return role_inlines.get(obj.role, [])
