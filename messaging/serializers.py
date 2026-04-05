from rest_framework import serializers
from .models import Conversation, ConversationParticipant, Message, MessageStatus
from accounts.serializers import UserMinimalSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'sender_avatar',
                  'content', 'message_type', 'is_deleted', 'created_at']
        read_only_fields = ['id', 'created_at', 'sender']


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user_detail = UserMinimalSerializer(source='user', read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'user_detail', 'role', 'joined_at', 'last_read_at', 'is_muted']


class ConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'title', 'created_at', 'updated_at',
                  'last_message', 'unread_count', 'other_participant']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {
                'content': msg.content[:100],
                'sender_name': msg.sender.full_name if msg.sender else None,
                'created_at': msg.created_at.isoformat(),
            }
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request', {})
        if hasattr(user, 'user'):
            user = user.user
        else:
            return 0
        try:
            participation = obj.participants.get(user=user)
            if participation.last_read_at:
                return obj.messages.filter(
                    created_at__gt=participation.last_read_at
                ).exclude(sender=user).count()
            return obj.messages.exclude(sender=user).count()
        except ConversationParticipant.DoesNotExist:
            return 0

    def get_other_participant(self, obj):
        if obj.type != 'direct':
            return None
        user = self.context.get('request', {})
        if hasattr(user, 'user'):
            user = user.user
        else:
            return None
        other = obj.participants.exclude(user=user).select_related('user').first()
        if other:
            return UserMinimalSerializer(other.user).data
        return None


class ConversationCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['direct', 'announcement'])
    title = serializers.CharField(required=False, allow_blank=True)
    participant_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    initial_message = serializers.CharField(required=False, allow_blank=True)
