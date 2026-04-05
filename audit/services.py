from .models import AuditLog
from .middleware import get_current_request


def log_action(user, action, target_type, target_id, details=None):
    """Create an audit log entry."""
    ip_address = None
    request = get_current_request()
    if request:
        ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
    AuditLog.objects.create(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
