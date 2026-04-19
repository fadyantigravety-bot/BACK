from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/church/', include('church.urls')),
    path('api/prayers/', include('prayers.urls')),
    path('api/friday-attendance/', include('friday_attendance.urls')),
    path('api/mass-attendance/', include('mass_attendance.urls')),
    path('api/confessions/', include('confessions.urls')),
    path('api/followups/', include('followups.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/audit/', include('audit.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
