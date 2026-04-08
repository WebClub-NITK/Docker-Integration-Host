from functools import wraps
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from hosts.models import UserHostRole


def _assigned_role_for_host(user, host_id):
    if host_id is None:
        return None

    # Direct match for access-host UUID based endpoints.
    role = UserHostRole.objects.filter(
        user=user,
        host_id=host_id,
    ).values_list('role', flat=True).first()
    if role:
        return role

    # Container endpoints use containers.Host integer IDs.
    # Resolve to hosts.Host by endpoint (ip_address + port).
    try:
        from containers.models import Host as ContainerHost
        from hosts.models import Host as AccessHost

        container_host = ContainerHost.objects.filter(pk=host_id).first()
        if not container_host:
            return None

        access_host = AccessHost.objects.filter(
            ip_address=container_host.ip_address,
            port=container_host.port,
        ).first()
        if not access_host:
            return None

        return UserHostRole.objects.filter(
            user=user,
            host=access_host,
        ).values_list('role', flat=True).first()
    except Exception:
        return None


def get_user_from_request(request):
    try:
        result = JWTAuthentication().authenticate(request)
    except (InvalidToken, TokenError):
        return None

    if result is None:
        return None
    user, _ = result
    return user


def check_role(user, host_id, allowed_roles):
    role_map = {
        'admin': 'ADMIN',
        'host': 'HOST_OWNER',
        'viewer': 'VIEWER',
    }

    if getattr(user, 'is_superuser', False):
        return True

    assigned_role = _assigned_role_for_host(user, host_id)
    if assigned_role:
        return assigned_role in allowed_roles

    normalized_role = role_map.get(getattr(user, 'role', '').lower())
    return normalized_role in allowed_roles


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        user = get_user_from_request(request)
        if not user or not user.is_authenticated:
            return Response(
                {'error': 'Unauthorized. Valid JWT required.'},
                status=401
            )
        request.user = user
        return view_func(self, request, *args, **kwargs)
    return wrapper


def require_role(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            host_id = kwargs.get('host_id')
            if not check_role(request.user, host_id, allowed_roles):
                return Response(
                    {'error': f'Forbidden. Required roles: {allowed_roles}'},
                    status=403
                )
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator