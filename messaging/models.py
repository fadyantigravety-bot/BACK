import uuid
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """A conversation thread — direct (1:1) or announcement (broadcast)."""

    class ConversationType(models.TextChoices):
        DIRECT = 'direct', 'محادثة مباشرة'
        ANNOUNCEMENT = 'announcement', 'إعلان'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField('النوع', max_length=15, choices=ConversationType.choices)
    title = models.CharField('العنوان', max_length=300, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_conversations', verbose_name='أنشأه',
    )
    is_active = models.BooleanField('نشط', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField('آخر تحديث', auto_now=True)

    class Meta:
        verbose_name = 'محادثة'
        verbose_name_plural = 'المحادثات'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'محادثة {self.id}'


class ConversationParticipant(models.Model):
    """Tracks who is in a conversation and their read state."""

    class ParticipantRole(models.TextChoices):
        OWNER = 'owner', 'مالك'
        PARTICIPANT = 'participant', 'مشارك'
        READONLY = 'readonly', 'قراءة فقط'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name='participants', verbose_name='المحادثة',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='conversation_participations', verbose_name='المستخدم',
    )
    role = models.CharField(
        'الدور', max_length=15,
        choices=ParticipantRole.choices, default=ParticipantRole.PARTICIPANT,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField('آخر قراءة', blank=True, null=True)
    is_muted = models.BooleanField('صامت', default=False)

    class Meta:
        verbose_name = 'مشارك في المحادثة'
        verbose_name_plural = 'المشاركون في المحادثات'
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f'{self.user} في {self.conversation}'


class Message(models.Model):
    """A single message within a conversation."""

    class MessageType(models.TextChoices):
        TEXT = 'text', 'نص'
        SYSTEM = 'system', 'نظام'
        ANNOUNCEMENT = 'announcement', 'إعلان'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name='messages', verbose_name='المحادثة',
        db_index=True,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='sent_messages', verbose_name='المرسل',
    )
    content = models.TextField('المحتوى')
    message_type = models.CharField(
        'نوع الرسالة', max_length=15,
        choices=MessageType.choices, default=MessageType.TEXT,
    )
    is_deleted = models.BooleanField('محذوف', default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} - {self.content[:50]}'


class MessageStatus(models.Model):
    """Per-recipient delivery and seen tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE,
        related_name='statuses', verbose_name='الرسالة',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='message_statuses', verbose_name='المستلم',
    )
    delivered_at = models.DateTimeField('وقت التسليم', blank=True, null=True)
    seen_at = models.DateTimeField('وقت القراءة', blank=True, null=True)

    class Meta:
        verbose_name = 'حالة الرسالة'
        verbose_name_plural = 'حالات الرسائل'
        unique_together = ('message', 'user')
