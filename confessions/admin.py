from django.contrib import admin
from .models import ConfessionRecord


@admin.register(ConfessionRecord)
class ConfessionRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'has_confessed', 'last_confession_date', 'is_overdue', 'recorded_by')
    list_filter = ('has_confessed', 'is_overdue')
    search_fields = ('member__first_name', 'member__last_name')
