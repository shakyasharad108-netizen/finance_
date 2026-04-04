"""
core/permissions.py

Role-based permission classes.

Architecture note:
Rather than scattering role checks throughout views, we define one permission
class per role requirement. Views declare their access level via
`permission_classes`, which keeps the authorisation intent explicit and testable.

Role hierarchy (additive):
  Viewer   → GET only
  Analyst  → GET + analytics endpoints
  Admin    → full CRUD + user management
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsViewer(BasePermission):
    """Allow read-only access. All authenticated users qualify at minimum."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.method in SAFE_METHODS
        )


class IsAnalystOrAbove(BasePermission):
    """Allow access to Analyst and Admin roles."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("analyst", "admin")
        )


class IsAdmin(BasePermission):
    """Restrict access to Admin role only."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Combined permission:
    - Any authenticated user may read (GET/HEAD/OPTIONS)
    - Only admins may write (POST/PUT/PATCH/DELETE)

    Used on FinancialRecord views so Viewers can browse but only Admins
    can create/update/delete.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "admin"
