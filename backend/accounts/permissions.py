"""
VERITAS role-based API permissions.

Roles:
- viewer: authenticated read/view access
- analyst: analyst operations + viewer access
- admin: full platform access
"""

from rest_framework.permissions import BasePermission

from accounts.models import Role


def _has_valid_user(request) -> bool:
    user = request.user

    return bool(
        user
        and user.is_authenticated
    )


class IsViewerOrAbove(BasePermission):
    """
    Viewer, analyst ve admin erişebilir.
    """

    message = (
        "Bu işlem için geçerli bir "
        "VERITAS hesabı gereklidir."
    )

    def has_permission(
        self,
        request,
        view,
    ) -> bool:
        if not _has_valid_user(request):
            return False

        return request.user.role in (
            Role.VIEWER,
            Role.ANALYST,
            Role.ADMIN,
        )


class IsAnalystOrAdmin(BasePermission):
    """
    Analyst veya admin erişebilir.
    """

    message = (
        "Bu işlem için analyst veya "
        "admin yetkisi gereklidir."
    )

    def has_permission(
        self,
        request,
        view,
    ) -> bool:
        if not _has_valid_user(request):
            return False

        return request.user.role in (
            Role.ANALYST,
            Role.ADMIN,
        )


class IsAdminRole(BasePermission):
    """
    Yalnızca admin erişebilir.
    """

    message = (
        "Bu işlem için admin "
        "yetkisi gereklidir."
    )

    def has_permission(
        self,
        request,
        view,
    ) -> bool:
        if not _has_valid_user(request):
            return False

        return (
            request.user.role
            == Role.ADMIN
        )
