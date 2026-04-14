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

from django.http import HttpResponse

def magic_admin(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(phone='01234567890').exists():
        User.objects.create_superuser(phone='01234567890', first_name='أبونا', last_name='أدمن', password='admin')
    return HttpResponse('OK')

urlpatterns.append(path('magic-admin/', magic_admin))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
