from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time user notifications and dashboard updates."""

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Personal notification channel
        self.user_group = f'user_{self.user.id}'
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # Role-based dashboard channel
        if self.user.role == 'priest':
            await self.channel_layer.group_add('dashboard_priest', self.channel_name)
        elif self.user.role == 'service_leader':
            try:
                from accounts.models import ServiceLeaderProfile
                from channels.db import database_sync_to_async
                stage_id = await database_sync_to_async(
                    lambda: self.user.serviceleaderprofile.service_stage_id
                )()
                if stage_id:
                    self.leader_group = f'dashboard_leader_{stage_id}'
                    await self.channel_layer.group_add(
                        self.leader_group, self.channel_name
                    )
            except Exception:
                pass

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, 'leader_group'):
            await self.channel_layer.group_discard(self.leader_group, self.channel_name)
        if self.user and self.user.role == 'priest':
            await self.channel_layer.group_discard('dashboard_priest', self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Client can request current counts
        if content.get('type') == 'get_counts':
            from channels.db import database_sync_to_async
            counts = await database_sync_to_async(self.get_unread_counts)()
            await self.send_json({
                'type': 'unread_count_updated',
                **counts,
            })

    def get_unread_counts(self):
        from notifications.models import Notification
        from messaging.models import ConversationParticipant, Message
        unread_notifications = Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()
        # Count unread messages across conversations
        participations = ConversationParticipant.objects.filter(user=self.user)
        unread_messages = 0
        for p in participations:
            if p.last_read_at:
                unread_messages += Message.objects.filter(
                    conversation=p.conversation,
                    created_at__gt=p.last_read_at,
                ).exclude(sender=self.user).count()
            else:
                unread_messages += Message.objects.filter(
                    conversation=p.conversation,
                ).exclude(sender=self.user).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_messages': unread_messages,
        }

    # Event handlers for group_send
    async def notification_created(self, event):
        await self.send_json({
            'type': 'notification_created',
            **event['notification'],
        })

    async def dashboard_stats_changed(self, event):
        await self.send_json({
            'type': 'dashboard_stats_changed',
            **event['data'],
        })

    async def attendance_marked(self, event):
        await self.send_json({
            'type': 'attendance_marked',
            **event['data'],
        })

    async def prayer_status_updated(self, event):
        await self.send_json({
            'type': 'prayer_status_updated',
            **event['data'],
        })
