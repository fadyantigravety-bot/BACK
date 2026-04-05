from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PriestProfile, ServiceLeaderProfile, ServantProfile, MemberProfile


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for references in other models."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone', 'first_name', 'last_name', 'full_name', 'role', 'avatar']


class PriestProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriestProfile
        fields = ['id', 'ordination_date', 'can_manage_confessions', 'notes']


class ServiceLeaderProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceLeaderProfile
        fields = ['id', 'service_stage', 'can_view_confession_status', 'appointed_date', 'notes']


class ServantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServantProfile
        fields = ['id', 'service_group', 'supervisor', 'can_view_prayer_data',
                  'can_view_mass_data', 'joined_service_date', 'notes']


class MemberProfileSerializer(serializers.ModelSerializer):
    assigned_servant_name = serializers.CharField(
        source='assigned_servant.full_name', read_only=True, default=None
    )
    service_group_name = serializers.CharField(
        source='service_group.name', read_only=True, default=None
    )

    class Meta:
        model = MemberProfile
        fields = ['id', 'date_of_birth', 'gender', 'address', 'guardian_name',
                  'guardian_phone', 'baptism_date', 'service_group', 'service_group_name',
                  'assigned_servant', 'assigned_servant_name', 'is_active_member',
                  'join_date', 'notes']


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user detail with role-specific profile."""
    full_name = serializers.CharField(read_only=True)
    priest_profile = PriestProfileSerializer(read_only=True)
    serviceleaderprofile = ServiceLeaderProfileSerializer(read_only=True)
    servant_profile = ServantProfileSerializer(read_only=True)
    member_profile = MemberProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'is_active', 'avatar', 'language', 'date_joined',
                  'priest_profile', 'serviceleaderprofile', 'servant_profile',
                  'member_profile']
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['phone', 'email', 'first_name', 'last_name', 'role', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['phone'], password=data['password'])
        if not user:
            raise serializers.ValidationError('بيانات الدخول غير صحيحة')
        if not user.is_active:
            raise serializers.ValidationError('الحساب غير نشط')
        data['user'] = user
        return data


class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()
    device_type = serializers.ChoiceField(choices=['android', 'ios'])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
