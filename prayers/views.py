from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from core.permissions import IsPriest, IsMember
from core.scoping import get_scoped_member_users
from .models import PrayerDefinition, PrayerLog
from .serializers import PrayerDefinitionSerializer, PrayerLogSerializer, PrayerLogUpdateSerializer


class PrayerDefinitionViewSet(viewsets.ModelViewSet):
    queryset = PrayerDefinition.objects.all()
    serializer_class = PrayerDefinitionSerializer
    filterset_fields = ['is_active']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsPriest()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PrayerLogViewSet(viewsets.ModelViewSet):
    serializer_class = PrayerLogSerializer
    filterset_fields = ['member', 'prayer', 'date', 'status']
    ordering_fields = ['date', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'member':
            return PrayerLog.objects.filter(member=user).select_related('prayer', 'member')
        member_ids = get_scoped_member_users(user)
        return PrayerLog.objects.filter(member_id__in=member_ids).select_related('prayer', 'member')

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return PrayerLogUpdateSerializer
        return PrayerLogSerializer

    @action(detail=False, methods=['get'])
    def my_today(self, request):
        """Get today's prayer logs for the authenticated member."""
        from datetime import datetime
        today = timezone.localdate()
        
        # Auto-generate if missing for active prayers
        active_prayers = PrayerDefinition.objects.filter(is_active=True)
        for prayer in active_prayers:
            scheduled_dt = timezone.make_aware(
                datetime.combine(today, prayer.scheduled_time)
            )
            PrayerLog.objects.get_or_create(
                member=request.user,
                prayer=prayer,
                date=today,
                defaults={
                    'status': 'pending',
                    'scheduled_time': scheduled_dt,
                },
            )
            
        logs = PrayerLog.objects.filter(
            member=request.user, date=today
        ).select_related('prayer')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Member updates their prayer response status."""
        log = self.get_object()
        if log.member != request.user:
            return Response({'error': 'غير مسموح'}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        if new_status not in ['completed', 'missed', 'snoozed', 'pending_confirmation']:
            return Response({'error': 'حالة غير صالحة'}, status=status.HTTP_400_BAD_REQUEST)
        log.status = new_status
        now = timezone.now()
        if new_status == 'completed':
            log.final_response_at = now
        elif new_status == 'snoozed':
            log.first_response_at = now
        log.save()
        # Broadcast to monitors via WebSocket
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'prayer_monitor',
                {
                    'type': 'prayer.status.updated',
                    'data': {
                        'member_id': str(log.member_id),
                        'prayer_id': str(log.prayer_id),
                        'date': str(log.date),
                        'status': new_status,
                    },
                },
            )
        except Exception:
            pass
        return Response(PrayerLogSerializer(log).data)
