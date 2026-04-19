from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from core.permissions import IsLeadership
from core.scoping import get_scoped_member_users
from notifications.services import create_notification
from .models import FollowUpRecord
from .serializers import FollowUpRecordSerializer


class FollowUpRecordViewSet(viewsets.ModelViewSet):
    serializer_class = FollowUpRecordSerializer
    filterset_fields = ['member', 'servant', 'type', 'priority', 'status']
    search_fields = ['summary', 'member__first_name', 'member__last_name']
    ordering_fields = ['date', 'priority', 'status', 'next_followup_date']

    def get_queryset(self):
        user = self.request.user
        qs = FollowUpRecord.objects.select_related('member', 'servant', 'created_by')
        if user.role == 'priest':
            return qs
        if user.role in ('service_leader', 'servant'):
            from django.db.models import Q
            member_ids = get_scoped_member_users(user)
            return qs.filter(Q(member_id__in=member_ids) | Q(servant=user))
        return qs.none()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsLeadership()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], permission_classes=[IsLeadership])
    def bulk_assign(self, request):
        member_ids = request.data.get('members', [])
        servant_ids = request.data.get('servants', [])
        f_type = request.data.get('type')
        priority = request.data.get('priority', 'medium')
        date = request.data.get('date')
        summary = request.data.get('summary', '')

        if not member_ids or not servant_ids or not date or not f_type:
            return Response({'error': 'Missing required fields: members, servants, date, type.'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        members = User.objects.filter(id__in=member_ids)
        servants = User.objects.filter(id__in=servant_ids)

        records_to_create = []
        for servant in servants:
            for member in members:
                records_to_create.append(FollowUpRecord(
                    member=member,
                    servant=servant,
                    type=f_type,
                    priority=priority,
                    date=date,
                    summary=summary,
                    status='pending',
                    created_by=request.user
                ))
        
        if records_to_create:
            FollowUpRecord.objects.bulk_create(records_to_create)

            for servant in servants:
                create_notification(
                    recipient=servant,
                    title="مهام متابعة جديدة",
                    body=f"تم تكليفك بمتابعة {len(members)} مخدومين جدد من قبل {request.user.first_name}",
                    notification_type='assignment',
                    reference_type='followup',
                )

        return Response({'message': f'تم تعيين {len(records_to_create)} مهمة بنجاح.'}, status=status.HTTP_201_CREATED)
