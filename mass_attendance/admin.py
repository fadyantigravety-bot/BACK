from django.contrib import admin
from .models import MassAttendanceRecord


@admin.register(MassAttendanceRecord)
class MassAttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('member', 'date', 'attended', 'church_name', 'mass_type')
    list_filter = ('attended', 'date')
    search_fields = ('member__first_name', 'member__last_name')
