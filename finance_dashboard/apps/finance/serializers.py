"""
finance/serializers.py

Serializers for Category and FinancialRecord.

Notes:
- `owner` is always set from `request.user` in the service layer,
  never accepted from client input — prevents ownership spoofing.
- `category_name` is a read-only convenience field so the client
  doesn't need a second request to resolve the category ID.
- Amount validation ensures no zero or negative values slip through.
"""

from rest_framework import serializers
from apps.finance.models import Category, FinancialRecord
from decimal import Decimal


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class FinancialRecordSerializer(serializers.ModelSerializer):
    """Full serializer for create/update operations."""

    category_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            "id", "title", "transaction_type", "amount",
            "date", "category", "category_name", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "category_name"]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_category(self, value):
        """Ensure the category belongs to the current user."""
        if value is None:
            return value
        request = self.context.get("request")
        if request and value.owner != request.user:
            raise serializers.ValidationError("Category does not belong to you.")
        return value


class FinancialRecordListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views — avoids fetching unnecessary fields
    and reduces payload size for paginated responses.
    """

    category_name = serializers.SerializerMethodField()

    class Meta:
        model = FinancialRecord
        fields = [
            "id", "title", "transaction_type", "amount",
            "date", "category_name", "created_at",
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


# ─── Dashboard / Analytics Serializers ───────────────────────────────────────

class DashboardSummarySerializer(serializers.Serializer):
    """Shape for the top-level summary numbers."""
    total_income = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    record_count = serializers.IntegerField()


class CategoryAggregationSerializer(serializers.Serializer):
    """Shape for category-wise breakdown rows."""
    category_id = serializers.UUIDField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    transaction_type = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()
