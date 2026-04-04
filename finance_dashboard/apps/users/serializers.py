"""
users/serializers.py

Serializers handle input validation and output shaping.

Key decisions:
- Passwords are write-only — never serialised out.
- Role is read-only for non-admins; the service layer enforces this.
- RegisterSerializer uses a confirm_password field for UX safety without
  storing it (it's validated then discarded).
"""

from rest_framework import serializers
from apps.users.models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    """Read serializer — used for list/retrieve responses."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    """Used for new user creation. Validates password confirmation."""

    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "confirm_password"]

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # Delegates to UserManager which hashes the password correctly
        return User.objects.create_user(**validated_data)


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Allows partial profile updates.
    Role change is intentionally excluded here — handled separately
    so it can be guarded by admin-only permission at the view/service level.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangeRoleSerializer(serializers.Serializer):
    """Dedicated serializer for admin role assignment — keeps intent explicit."""

    role = serializers.ChoiceField(choices=UserRole.choices)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError(
                {"confirm_new_password": "New passwords do not match."}
            )
        return data
