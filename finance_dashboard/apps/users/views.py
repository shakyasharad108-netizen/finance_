"""
users/views.py

Thin views. Each view:
1. Validates input via serializer
2. Delegates logic to UserService
3. Returns a shaped response

No business logic here — that belongs in services.py.
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.permissions import IsAdmin
from apps.core.responses import success_response, created_response, error_response
from apps.core.exceptions import ServiceError

from apps.users.serializers import (
    RegisterSerializer, UserSerializer,
    UpdateUserSerializer, ChangeRoleSerializer, ChangePasswordSerializer,
)
from apps.users.services import UserService


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — public endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            user = UserService.register_user(serializer.validated_data)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)

        return created_response(UserSerializer(user).data, "Account created successfully.")


class LoginView(APIView):
    """POST /api/v1/auth/login/ — returns JWT pair."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return error_response("Email and password are required.")

        from django.contrib.auth import authenticate
        user = authenticate(request, username=email, password=password)

        if not user:
            return error_response("Invalid credentials.", status_code=401)
        if not user.is_active:
            return error_response("Account is deactivated.", status_code=403)

        refresh = RefreshToken.for_user(user)
        return success_response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            "Login successful.",
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklists the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response("Refresh token is required.")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return error_response("Invalid or already blacklisted token.")
        return success_response(message="Logged out successfully.")


class MeView(APIView):
    """GET/PATCH /api/v1/auth/me/ — current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateUserSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        user = serializer.save()
        return success_response(UserSerializer(user).data, "Profile updated.")


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        try:
            UserService.change_password(
                request.user,
                serializer.validated_data["old_password"],
                serializer.validated_data["new_password"],
            )
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(message="Password changed successfully.")


# ─── Admin User Management ────────────────────────────────────────────────────

class UserListView(APIView):
    """GET /api/v1/users/ — admin only."""
    permission_classes = [IsAdmin]

    def get(self, request):
        users = UserService.get_all_users()
        return success_response(UserSerializer(users, many=True).data)


class UserDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/users/<id>/ — admin only."""
    permission_classes = [IsAdmin]

    def _get_user(self, user_id):
        try:
            return UserService.get_user_by_id(user_id)
        except ServiceError as e:
            return None, error_response(e.message, status_code=e.status_code)

    def get(self, request, user_id):
        user, err = self._get_user(user_id)
        if err:
            return err
        return success_response(UserSerializer(user).data)

    def patch(self, request, user_id):
        user, err = self._get_user(user_id)
        if err:
            return err
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        user = serializer.save()
        return success_response(UserSerializer(user).data, "User updated.")

    def delete(self, request, user_id):
        user, err = self._get_user(user_id)
        if err:
            return err
        try:
            UserService.deactivate_user(user, request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(message="User deactivated.")


class ChangeUserRoleView(APIView):
    """PATCH /api/v1/users/<id>/role/ — admin only."""
    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        try:
            user = UserService.get_user_by_id(user_id)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)

        serializer = ChangeRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            user = UserService.change_role(user, serializer.validated_data["role"], request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)

        return success_response(UserSerializer(user).data, "Role updated.")
