from django.contrib import admin
from .models import ServiceStage, ServiceGroup


@admin.register(ServiceStage)
class ServiceStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage', 'leader', 'is_active')
    list_filter = ('stage', 'is_active')
    search_fields = ('name',)
