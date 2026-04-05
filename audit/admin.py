from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_type', 'target_id', 'ip_address', 'created_at')
    list_filter = ('action', 'target_type')
    search_fields = ('user__first_name', 'action')
    readonly_fields = ('user', 'action', 'target_type', 'target_id', 'details', 'ip_address', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
