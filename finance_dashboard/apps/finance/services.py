"""
finance/services.py

All business logic for financial records and dashboard analytics.

Architecture rationale:
- Views call service methods; they never touch models directly.
- Each method is a pure function from (user, data) → (result | exception).
- This makes the logic unit-testable without HTTP overhead.
- Admin users see ALL records; others see only their own.
  This data-scoping decision lives here, not in views.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Q, DecimalField
from django.db.models.functions import Coalesce

from apps.finance.models import FinancialRecord, Category, TransactionType
from apps.users.models import User, UserRole
from apps.core.exceptions import ServiceError, PermissionDeniedError


class RecordService:
    """CRUD operations for FinancialRecord."""

    @staticmethod
    def _base_queryset(user: User):
        """
        Scope queryset by role.
        Admins see everything; Analysts and Viewers see only their own records.
        """
        qs = FinancialRecord.objects.select_related("category", "owner")
        if user.role != UserRole.ADMIN:
            qs = qs.filter(owner=user)
        return qs

    @staticmethod
    def list_records(user: User, filters: dict = None) -> "QuerySet":
        return RecordService._base_queryset(user)

    @staticmethod
    def get_record(record_id: str, user: User) -> FinancialRecord:
        try:
            record = RecordService._base_queryset(user).get(id=record_id)
        except FinancialRecord.DoesNotExist:
            raise ServiceError("Record not found.", status_code=404)
        return record

    @staticmethod
    def create_record(user: User, validated_data: dict) -> FinancialRecord:
        """
        Only Admins and Analysts can create records.
        Viewer role is read-only.
        """
        if user.role == UserRole.VIEWER:
            raise PermissionDeniedError("Viewers cannot create financial records.")
        record = FinancialRecord.objects.create(owner=user, **validated_data)
        return record

    @staticmethod
    def update_record(record_id: str, user: User, validated_data: dict) -> FinancialRecord:
        """
        Update a record.
        - Admins can update any record.
        - Analysts can only update their own records.
        - Viewers cannot update.
        """
        if user.role == UserRole.VIEWER:
            raise PermissionDeniedError("Viewers cannot modify financial records.")

        record = RecordService.get_record(record_id, user)

        # Analyst can only edit their own records (already scoped in _base_queryset)
        for attr, value in validated_data.items():
            setattr(record, attr, value)
        record.save()
        return record

    @staticmethod
    def delete_record(record_id: str, user: User) -> None:
        """
        Only Admins can delete records.
        Uses soft delete so audit trail is preserved.
        """
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only Admins can delete financial records.")

        record = RecordService.get_record(record_id, user)
        record.soft_delete()


class CategoryService:
    """CRUD for user-owned categories."""

    @staticmethod
    def list_categories(user: User):
        qs = Category.objects.filter(owner=user)
        return qs

    @staticmethod
    def get_category(category_id: str, user: User) -> Category:
        try:
            return Category.objects.get(id=category_id, owner=user)
        except Category.DoesNotExist:
            raise ServiceError("Category not found.", status_code=404)

    @staticmethod
    def create_category(user: User, validated_data: dict) -> Category:
        if Category.objects.filter(name=validated_data["name"], owner=user).exists():
            raise ServiceError("A category with this name already exists.")
        return Category.objects.create(owner=user, **validated_data)

    @staticmethod
    def update_category(category_id: str, user: User, validated_data: dict) -> Category:
        category = CategoryService.get_category(category_id, user)
        for attr, value in validated_data.items():
            setattr(category, attr, value)
        category.save()
        return category

    @staticmethod
    def delete_category(category_id: str, user: User) -> None:
        category = CategoryService.get_category(category_id, user)
        category.soft_delete()


class DashboardService:
    """
    Analytics queries for the dashboard.
    Only Analysts and Admins may call these.

    Using Django's ORM aggregations rather than raw SQL keeps the code
    portable across databases and automatically respects the soft-delete
    manager (is_deleted=False is always filtered out).
    """

    @staticmethod
    def _get_scoped_qs(user: User):
        """Dashboard analytics respect the same data-scoping rules as records."""
        qs = FinancialRecord.objects.all()
        if user.role != UserRole.ADMIN:
            qs = qs.filter(owner=user)
        return qs

    @staticmethod
    def get_summary(user: User, date_from=None, date_to=None) -> dict:
        """
        Returns total income, total expense, net balance, and record count.
        Coalesce(Sum(...), 0) prevents None when there are no records.
        """
        if not user.is_analyst:
            raise PermissionDeniedError("Only Analysts and Admins can access the dashboard.")

        qs = DashboardService._get_scoped_qs(user)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        aggregation = qs.aggregate(
            total_income=Coalesce(
                Sum("amount", filter=Q(transaction_type=TransactionType.INCOME)),
                Decimal("0"),
                output_field=DecimalField(),
            ),
            total_expense=Coalesce(
                Sum("amount", filter=Q(transaction_type=TransactionType.EXPENSE)),
                Decimal("0"),
                output_field=DecimalField(),
            ),
            record_count=Count("id"),
        )
        aggregation["net_balance"] = aggregation["total_income"] - aggregation["total_expense"]
        return aggregation

    @staticmethod
    def get_category_breakdown(user: User, date_from=None, date_to=None) -> list:
        """
        Returns amount and count grouped by (category, transaction_type).
        Records without a category are grouped under category_name=None.
        """
        if not user.is_analyst:
            raise PermissionDeniedError("Only Analysts and Admins can access analytics.")

        qs = DashboardService._get_scoped_qs(user)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        rows = (
            qs.values(
                "category__id",
                "category__name",
                "transaction_type",
            )
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        return [
            {
                "category_id": row["category__id"],
                "category_name": row["category__name"] or "Uncategorised",
                "transaction_type": row["transaction_type"],
                "total": row["total"],
                "count": row["count"],
            }
            for row in rows
        ]

    @staticmethod
    def get_recent_transactions(user: User, limit: int = 10) -> "QuerySet":
        """Returns the N most recent transactions for the dashboard feed."""
        if not user.is_analyst:
            raise PermissionDeniedError("Only Analysts and Admins can access the dashboard.")

        return (
            DashboardService._get_scoped_qs(user)
            .select_related("category")
            .order_by("-date", "-created_at")[:limit]
        )
