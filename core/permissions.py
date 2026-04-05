from rest_framework.permissions import BasePermission


class IsPriest(BasePermission):
    """Allow access only to Priest users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'priest'
        )


class IsServiceLeader(BasePermission):
    """Allow access only to Service Leader users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'service_leader'
        )


class IsServant(BasePermission):
    """Allow access only to Servant users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'servant'
        )


class IsMember(BasePermission):
    """Allow access only to Member users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'member'
        )


class IsPriestOrServiceLeader(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('priest', 'service_leader')
        )


class IsLeadership(BasePermission):
    """Priest or Service Leader or Servant."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('priest', 'service_leader', 'servant')
        )


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: allow edit only if user owns the object."""
    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.user == request.user or obj.created_by == request.user
