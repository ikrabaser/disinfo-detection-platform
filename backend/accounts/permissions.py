"""
Basit RBAC (Role-Based Access Control) icin DRF permission siniflari.

Kullanim:
    class SomeView(APIView):
        permission_classes = [IsAnalystOrAdmin]

Ayrica `agent` uygulamasindaki her tool, hangi rollerin bu tool'u
cagirabilecegini beyan eder (bkz. agent/tools/permissions.py). Bu modul,
o mekanizmanin da temelini olusturan `has_role` yardimci fonksiyonunu icerir.
"""
from rest_framework.permissions import BasePermission

ROLE_HIERARCHY = {
    "admin": {"admin", "analyst", "viewer"},
    "analyst": {"analyst", "viewer"},
    "viewer": {"viewer"},
}


def has_role(user, allowed_roles) -> bool:
    """Kullanicinin rolu, verilen `allowed_roles` kumesinden biriyle eslesiyor mu?"""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    user_role = getattr(user, "role", None)
    if user_role is None:
        return False
    return user_role in allowed_roles


class RoleRequiredPermission(BasePermission):
    """Bir view uzerinde `allowed_roles` class attribute'u bekleyen genel permission sinifi."""

    allowed_roles: set[str] = {"admin", "analyst", "viewer"}

    def has_permission(self, request, view):
        allowed = getattr(view, "allowed_roles", self.allowed_roles)
        return has_role(request.user, allowed)


class IsAdmin(RoleRequiredPermission):
    allowed_roles = {"admin"}


class IsAnalystOrAdmin(RoleRequiredPermission):
    allowed_roles = {"admin", "analyst"}


class IsViewerOrAbove(RoleRequiredPermission):
    allowed_roles = {"admin", "analyst", "viewer"}
