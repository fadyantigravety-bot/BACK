from django.contrib import admin
from .models import FridayMeetingSession, FridayAttendanceRecord


class AttendanceInline(admin.TabularInline):
    model = FridayAttendanceRecord
    extra = 0


@admin.register(FridayMeetingSession)
class FridayMeetingSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'service_stage', 'is_locked')
    list_filter = ('is_locked', 'service_stage')
    inlines = [AttendanceInline]


@admin.register(FridayAttendanceRecord)
class FridayAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'session', 'status', 'marked_by', 'marked_at')
    list_filter = ('status', 'session__date')
    search_fields = ('member__first_name', 'member__last_name')
