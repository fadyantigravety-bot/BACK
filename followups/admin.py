from django.contrib import admin
from .models import FollowUpRecord


@admin.register(FollowUpRecord)
class FollowUpRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'servant', 'type', 'date', 'priority', 'status')
    list_filter = ('type', 'priority', 'status')
    search_fields = ('member__first_name', 'member__last_name', 'summary')
