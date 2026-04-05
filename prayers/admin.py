from django.contrib import admin
from .models import PrayerDefinition, PrayerLog


@admin.register(PrayerDefinition)
class PrayerDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'scheduled_time', 'order', 'is_active')
    list_filter = ('is_active',)


@admin.register(PrayerLog)
class PrayerLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'prayer', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('member__first_name', 'member__last_name')
