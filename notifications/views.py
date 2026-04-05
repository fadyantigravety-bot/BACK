from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import User, ServantProfile, ServiceLeaderProfile
from core.scoping import get_scoped_members
from .models import Notification
from .serializers import NotificationSerializer
from .services import send_bulk_push


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    filterset_fields = ['notification_type', 'is_read']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'تم'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'status': 'تم تحديث جميع الإشعارات'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({'unread_count': count})

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        user = request.user
        if user.role == 'member':
            return Response({'error': 'غير مسموح لك بإرسال إشعارات'}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title')
        body = request.data.get('body')
        target_roles = request.data.get('target_roles', [])
        meeting_type = request.data.get('meeting_type') # 'university' or 'high_school'

        if not title or not body or not target_roles:
            return Response({'error': 'Title, body, and target_roles are required.'}, status=status.HTTP_400_BAD_REQUEST)

        target_users = set()

        if 'member' in target_roles:
            members = get_scoped_members(user)
            if meeting_type:
                members = members.filter(meeting_type=meeting_type)
            target_users.update(members.values_list('user_id', flat=True))

        if 'servant' in target_roles:
            if user.role == 'priest':
                servants = User.objects.filter(role='servant', is_active=True).values_list('id', flat=True)
                target_users.update(servants)
            elif user.role == 'service_leader':
                try:
                    leader_profile = user.serviceleaderprofile
                    servants = ServantProfile.objects.filter(service_group__stage=leader_profile.service_stage).values_list('user_id', flat=True)
                    target_users.update(servants)
                except Exception:
                    pass

        if 'service_leader' in target_roles:
            if user.role == 'priest':
                leaders = User.objects.filter(role='service_leader', is_active=True).values_list('id', flat=True)
                target_users.update(leaders)

        users_to_notify = User.objects.filter(id__in=target_users)
        
        if not users_to_notify.exists():
            return Response({'message': 'لا يوجد مستخدمين لإرسال الإشعار لهم'}, status=status.HTTP_200_OK)

        send_bulk_push(
            users=users_to_notify,
            title=title,
            body=body,
            notification_type=Notification.NotificationType.ANNOUNCEMENT
        )

        return Response({'success': True, 'notified_count': users_to_notify.count()})
