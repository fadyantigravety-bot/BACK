import logging
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)

import requests

def send_push_notification(user, title, body, data=None):
    """Send a push notification via OneSignal to a specific user using external_id."""
    app_id = getattr(settings, 'ONESIGNAL_APP_ID', None)
    rest_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', None)
    
    if not app_id or not rest_key:
        logger.warning('OneSignal credentials not set. Push disabled.')
        return False
        
    if not user.notifications_enabled:
        return False

    url = "https://onesignal.com/api/v1/notifications"
    
    payload = {
        "app_id": app_id,
        "target_channel": "push",
        "include_aliases": {
            "external_id": [str(user.id)]
        },
        "headings": {"en": title, "ar": title},
        "contents": {"en": body, "ar": body},
        "data": data or {},
        "small_icon": "ic_notification",
        "large_icon": "ic_large_notification",
        "android_accent_color": "FF1B5E7B",
        "android_led_color": "FF1B5E7B",
    }
    
    headers = {
        "accept": "application/json",
        "Authorization": f"Basic {rest_key}",
        "content-type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        # OneSignal returns 200 with an 'errors' list if targets are invalid
        if response.status_code == 200:
            res_data = response.json()
            if 'errors' in res_data:
                logger.error(f'OneSignal send warning/error for {user.id}: {res_data["errors"]}')
                return False
            return True
        else:
            logger.error(f'OneSignal send failed for {user.id}. Code: {response.status_code}, Body: {response.text}')
            return False
    except Exception as e:
        logger.error(f'OneSignal API request failed: {e}')
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
    """Send push notifications to multiple users using OneSignal bulk."""
    if not users:
        return

    # First, create in-app notifications
    notifications_to_create = []
    user_ids = []
    
    for user in users:
        notifications_to_create.append(
            Notification(
                recipient=user,
                title=title,
                body=body,
                notification_type=notification_type,
                is_pushed=True
            )
        )
        if user.notifications_enabled:
            user_ids.append(str(user.id))
            
    Notification.objects.bulk_create(notifications_to_create)

    # Next, send one bulk request to OneSignal
    app_id = getattr(settings, 'ONESIGNAL_APP_ID', None)
    rest_key = getattr(settings, 'ONESIGNAL_REST_API_KEY', None)
    
    if app_id and rest_key and user_ids:
        # OneSignal limits aliases to 2000 per request, batching if necessary
        chunk_size = 2000
        for i in range(0, len(user_ids), chunk_size):
            chunk_ids = user_ids[i:i + chunk_size]
            url = "https://onesignal.com/api/v1/notifications"
            payload = {
                "app_id": app_id,
                "target_channel": "push",
                "include_aliases": {
                    "external_id": chunk_ids
                },
                "headings": {"en": title, "ar": title},
                "contents": {"en": body, "ar": body},
                "data": data or {"type": notification_type},
                "small_icon": "ic_notification",
                "large_icon": "ic_large_notification",
                "android_accent_color": "FF1B5E7B",
                "android_led_color": "FF1B5E7B",
            }
            headers = {
                "accept": "application/json",
                "Authorization": f"Basic {rest_key}",
                "content-type": "application/json"
            }
            try:
                requests.post(url, json=payload, headers=headers, timeout=10)
            except Exception as e:
                logger.error(f'OneSignal bulk push failed: {e}')
