from accounts.models import MemberProfile


def get_scoped_members(user):
    """Return a queryset of MemberProfiles scoped to the user's role.

    - Priest: all members
    - Service Leader: members in their service stage groups
    - Servant: only assigned members
    - Member: only self
    """
    if user.role == 'priest' or user.is_superuser:
        return MemberProfile.objects.all()

    if user.role == 'service_leader':
        try:
            leader_profile = user.serviceleaderprofile
            return MemberProfile.objects.filter(
                service_group__stage=leader_profile.service_stage
            )
        except Exception:
            return MemberProfile.objects.all()

    if user.role == 'servant':
        from django.db.models import Q
        try:
            servant_group = user.servant_profile.service_group
            if servant_group and servant_group.stage:
                return MemberProfile.objects.filter(
                    Q(assigned_servant=user) | Q(service_group__stage=servant_group.stage)
                ).distinct()
            elif servant_group:
                return MemberProfile.objects.filter(
                    Q(assigned_servant=user) | Q(service_group=servant_group)
                ).distinct()
            else:
                return MemberProfile.objects.filter(assigned_servant=user)
        except Exception:
            return MemberProfile.objects.filter(assigned_servant=user)

    if user.role == 'member':
        return MemberProfile.objects.filter(user=user)

    return MemberProfile.objects.none()


def get_scoped_member_users(user):
    """Return User IDs of members in scope."""
    return get_scoped_members(user).values_list('user_id', flat=True)
