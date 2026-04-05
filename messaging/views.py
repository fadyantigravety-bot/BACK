from rest_framework import viewsets, status as http_status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    ConversationListSerializer, ConversationCreateSerializer,
    MessageSerializer, ConversationParticipantSerializer,
)
from accounts.models import User
from notifications.services import create_notification


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationListSerializer
    search_fields = ['title']

    def get_queryset(self):
        return Conversation.objects.filter(
            participants__user=self.request.user,
            is_active=True
        ).distinct().prefetch_related('participants', 'messages')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

    def create(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # For direct chats, check existing conversation
        if data['type'] == 'direct' and len(data['participant_ids']) == 1:
            other_id = data['participant_ids'][0]
            existing = Conversation.objects.filter(
                type='direct',
                participants__user=request.user,
            ).filter(participants__user_id=other_id)
            if existing.exists():
                conv = existing.first()
                return Response(
                    ConversationListSerializer(conv, context={'request': request}).data
                )

        conv = Conversation.objects.create(
            type=data['type'],
            title=data.get('title', ''),
            created_by=request.user,
        )
        ConversationParticipant.objects.create(
            conversation=conv, user=request.user, role='owner'
        )
        for uid in data['participant_ids']:
            ConversationParticipant.objects.get_or_create(
                conversation=conv,
                user_id=uid,
                defaults={'role': 'participant'},
            )

        if data.get('initial_message'):
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=data['initial_message'],
            )

        return Response(
            ConversationListSerializer(conv, context={'request': request}).data,
            status=http_status.HTTP_201_CREATED,
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return Message.objects.filter(
            conversation_id=conversation_id,
            conversation__participants__user=self.request.user,
            is_deleted=False,
        ).select_related('sender')

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        msg = serializer.save(
            sender=self.request.user,
            conversation_id=conversation_id,
        )
        Conversation.objects.filter(id=conversation_id).update(updated_at=timezone.now())
        # Notify participants
        participants = ConversationParticipant.objects.filter(
            conversation_id=conversation_id
        ).exclude(user=self.request.user).select_related('user')
        for p in participants:
            if not p.is_muted:
                create_notification(
                    recipient=p.user,
                    title='رسالة جديدة',
                    body=f'{self.request.user.full_name}: {msg.content[:80]}',
                    notification_type='message',
                    reference_type='Conversation',
                    reference_id=conversation_id,
                )

    @action(detail=False, methods=['post'])
    def mark_read(self, request, conversation_id=None):
        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=request.user,
        ).update(last_read_at=timezone.now())
        return Response({'status': 'تم'})
