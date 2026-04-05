from accounts.models import MemberProfile


def get_scoped_members(user):
    """Return a queryset of MemberProfiles scoped to the user's role.

    - Priest: all members
    - Service Leader: members in their service stage groups
    - Servant: only assigned members
    - Member: only self
    """
    if user.role == 'priest':
        return MemberProfile.objects.all()

    if user.role == 'service_leader':
        try:
            leader_profile = user.serviceleaderprofile
            return MemberProfile.objects.filter(
                service_group__stage=leader_profile.service_stage
            )
        except Exception:
            return MemberProfile.objects.none()

    if user.role == 'servant':
        return MemberProfile.objects.filter(assigned_servant=user)

    if user.role == 'member':
        return MemberProfile.objects.filter(user=user)

    return MemberProfile.objects.none()


def get_scoped_member_users(user):
    """Return User IDs of members in scope."""
    return get_scoped_members(user).values_list('user_id', flat=True)
