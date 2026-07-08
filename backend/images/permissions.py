from rest_framework.permissions import SAFE_METHODS, BasePermission
from hosts.models import UserHostRole


def _host_assignment_role(user, host_id):
    if not host_id:
        return None
    return UserHostRole.objects.filter(
        user=user,
        host_id=host_id,
    ).values_list('role', flat=True).first()


class IsAdminOrHostOwner(BasePermission):
    """
    POST (enqueue pull): only admin or the host owner.
    Safe methods (GET list/detail): any authenticated user.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.role == "admin":
            return True

        host_id = view.kwargs.get("host_id")
        assigned_role = _host_assignment_role(request.user, host_id)

        if request.method in SAFE_METHODS:
            return assigned_role in {"VIEWER", "HOST_OWNER", "ADMIN"}

        return assigned_role == "ADMIN"

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.role == "admin":
            return True

        assigned_role = _host_assignment_role(request.user, getattr(obj, "host_id", None))
        if request.method in SAFE_METHODS:
            return assigned_role in {"VIEWER", "HOST_OWNER", "ADMIN"}

        return assigned_role == "ADMIN"


class IsAdminOnly(BasePermission):
    """DELETE (cancel): admin only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == "admin"
