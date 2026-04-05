from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import IsPriest, IsPriestOrServiceLeader
from .models import User, PriestProfile, ServiceLeaderProfile, ServantProfile, MemberProfile
from .serializers import (
    UserDetailSerializer, UserMinimalSerializer, UserCreateSerializer,
    LoginSerializer, FCMTokenSerializer, ChangePasswordSerializer,
    MemberProfileSerializer,
)


class LoginView(generics.GenericAPIView):
    """Phone + password login, returns JWT tokens."""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserDetailSerializer(user).data,
        })


class RegisterView(generics.CreateAPIView):
    """Create a new user account."""
    serializer_class = UserCreateSerializer
    permission_classes = [IsPriest]

    def perform_create(self, serializer):
        user = serializer.save()
        # Auto-create role profile
        role = user.role
        if role == 'priest':
            PriestProfile.objects.create(user=user)
        elif role == 'service_leader':
            ServiceLeaderProfile.objects.create(user=user)
        elif role == 'servant':
            ServantProfile.objects.create(user=user)
        elif role == 'member':
            MemberProfile.objects.create(
                user=user,
                date_of_birth=self.request.data.get('date_of_birth', '2000-01-01'),
                gender=self.request.data.get('gender', 'male'),
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UpdateFCMTokenView(generics.GenericAPIView):
    """Register or update FCM device token."""
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.device_type = serializer.validated_data['device_type']
        request.user.save(update_fields=['fcm_token', 'device_type'])
        return Response({'status': 'تم تحديث التوكن'})


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'كلمة المرور القديمة غير صحيحة'},
                            status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'status': 'تم تغيير كلمة المرور'})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve users (scoped by role)."""
    serializer_class = UserMinimalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'priest':
            return User.objects.all()
        elif user.role == 'service_leader':
            try:
                from django.db.models import Q
                stage = user.serviceleaderprofile.service_stage
                return User.objects.filter(
                    Q(member_profile__service_group__stage=stage) |
                    Q(servant_profile__service_group__stage=stage)
                ).distinct()
            except Exception:
                return User.objects.none()
        elif user.role == 'servant':
            member_ids = MemberProfile.objects.filter(
                assigned_servant=user
            ).values_list('user_id', flat=True)
            return User.objects.filter(id__in=member_ids)
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserMinimalSerializer
