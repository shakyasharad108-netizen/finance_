"""
users/services.py

Service layer — all business logic lives here, not in views.

Why a service layer?
- Views become thin request/response handlers.
- Business logic is testable in isolation (no request object needed).
- Logic can be reused across views, management commands, Celery tasks, etc.
"""

from django.contrib.auth import authenticate
from apps.users.models import User, UserRole
from apps.core.exceptions import ServiceError, PermissionDeniedError


class UserService:

    @staticmethod
    def register_user(validated_data: dict) -> User:
        """
        Create a new user.
        New users always start as Viewer — role escalation requires admin action.
        """
        validated_data["role"] = UserRole.VIEWER
        user = User.objects.create_user(**validated_data)
        return user

    @staticmethod
    def get_all_users() -> "QuerySet":
        """Return all active users. Admin-only operation."""
        return User.objects.filter(is_active=True).order_by("-date_joined")

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise ServiceError("User not found.", status_code=404)

    @staticmethod
    def update_user(user: User, validated_data: dict) -> User:
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save()
        return user

    @staticmethod
    def change_role(target_user: User, new_role: str, requesting_user: User) -> User:
        """
        Only admins may change roles.
        Admins cannot demote themselves — prevents accidental lockout.
        """
        if requesting_user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only admins can change user roles.")

        if str(target_user.id) == str(requesting_user.id) and new_role != UserRole.ADMIN:
            raise ServiceError("Admins cannot remove their own admin role.")

        target_user.role = new_role
        target_user.save(update_fields=["role", "updated_at"])
        return target_user

    @staticmethod
    def deactivate_user(target_user: User, requesting_user: User) -> None:
        """Soft-deactivate (block login) without deleting the account."""
        if str(target_user.id) == str(requesting_user.id):
            raise ServiceError("You cannot deactivate your own account.")
        target_user.is_active = False
        target_user.save(update_fields=["is_active", "updated_at"])

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> None:
        if not user.check_password(old_password):
            raise ServiceError("Current password is incorrect.")
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
