import logging
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)

# Lazy Firebase initialization
_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            import firebase_admin
            from firebase_admin import credentials
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if cred_path:
                cred = credentials.Certificate(cred_path)
                _firebase_app = firebase_admin.initialize_app(cred)
            else:
                logger.warning('FIREBASE_CREDENTIALS_PATH not set. FCM disabled.')
        except Exception as e:
            logger.error(f'Firebase init failed: {e}')
    return _firebase_app


def send_push_notification(user, title, body, data=None):
    """Send a push notification via FCM to a specific user."""
    if not user.fcm_token or not user.notifications_enabled:
        return False

    app = _get_firebase_app()
    if app is None:
        return False

    try:
        from firebase_admin import messaging as fcm
        message = fcm.Message(
            notification=fcm.Notification(title=title, body=body),
            data=data or {},
            token=user.fcm_token,
        )
        fcm.send(message)
        return True
    except Exception as e:
        logger.error(f'FCM send failed for {user.id}: {e}')
        # Invalidate stale token
        if 'NOT_FOUND' in str(e) or 'UNREGISTERED' in str(e):
            user.fcm_token = None
            user.save(update_fields=['fcm_token'])
        return False


def create_notification(recipient, title, body, notification_type,
                        reference_type=None, reference_id=None,
                        send_push=True):
    """Create an in-app notification and optionally send FCM push."""
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        body=body,
        notification_type=notification_type,
        reference_type=reference_type,
        reference_id=reference_id,
    )

    if send_push:
        pushed = send_push_notification(
            recipient, title, body,
            data={
                'type': notification_type,
                'notification_id': str(notification.id),
                'reference_type': reference_type or '',
                'reference_id': str(reference_id) if reference_id else '',
            },
        )
        if pushed:
            notification.is_pushed = True
            notification.save(update_fields=['is_pushed'])

    # Send via WebSocket for in-app delivery
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{recipient.id}',
            {
                'type': 'notification.created',
                'notification': {
                    'id': str(notification.id),
                    'title': title,
                    'body': body,
                    'notification_type': notification_type,
                    'created_at': notification.created_at.isoformat(),
                },
            },
        )
    except Exception as e:
        logger.warning(f'WebSocket notification send failed: {e}')

    return notification


def send_bulk_push(users, title, body, notification_type, data=None):
    """Send push notifications to multiple users."""
    for user in users:
        create_notification(
            recipient=user,
            title=title,
            body=body,
            notification_type=notification_type,
        )
