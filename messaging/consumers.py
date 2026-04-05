import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time chat."""

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group = f'chat_{self.conversation_id}'
        self.user = self.scope.get('user')

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # Verify user is participant
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type', 'chat_message')

        if message_type == 'chat_message':
            message_data = await self.save_message(content.get('content', ''))
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'chat.message',
                    'message': message_data,
                },
            )
        elif message_type == 'mark_seen':
            await self.mark_messages_seen()
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'chat.seen',
                    'user_id': str(self.user.id),
                    'seen_at': timezone.now().isoformat(),
                },
            )

    async def chat_message(self, event):
        await self.send_json(event['message'])

    async def chat_seen(self, event):
        await self.send_json({
            'type': 'message_seen',
            'user_id': event['user_id'],
            'seen_at': event['seen_at'],
        })

    @database_sync_to_async
    def check_participant(self):
        from messaging.models import ConversationParticipant
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        from messaging.models import Message, Conversation
        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender=self.user,
            content=content,
            message_type='text',
        )
        # Update conversation timestamp
        Conversation.objects.filter(id=self.conversation_id).update(
            updated_at=timezone.now()
        )
        return {
            'type': 'message_sent',
            'id': str(message.id),
            'conversation_id': str(self.conversation_id),
            'sender_id': str(self.user.id),
            'sender_name': self.user.full_name,
            'content': content,
            'created_at': message.created_at.isoformat(),
        }

    @database_sync_to_async
    def mark_messages_seen(self):
        from messaging.models import ConversationParticipant
        ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
        ).update(last_read_at=timezone.now())
