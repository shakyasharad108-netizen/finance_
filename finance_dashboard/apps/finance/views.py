"""
finance/views.py

Thin views that:
  1. Authenticate via JWT (enforced by DEFAULT_PERMISSION_CLASSES)
  2. Validate input via serializers
  3. Delegate to service layer
  4. Return shaped responses

Access control is enforced in the service layer per method,
so views stay free of role-check conditionals.
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from apps.core.responses import success_response, created_response, error_response
from apps.core.exceptions import ServiceError, PermissionDeniedError
from apps.core.pagination import StandardPagination

from apps.finance.models import FinancialRecord, Category
from apps.finance.serializers import (
    FinancialRecordSerializer, FinancialRecordListSerializer,
    CategorySerializer, DashboardSummarySerializer, CategoryAggregationSerializer,
)
from apps.finance.services import RecordService, CategoryService, DashboardService
from apps.finance.filters import FinancialRecordFilter


# ─── Financial Records ────────────────────────────────────────────────────────

class FinancialRecordListCreateView(APIView):
    """
    GET  /api/v1/finance/records/   — list (all roles)
    POST /api/v1/finance/records/   — create (analyst, admin)

    Pagination is handled manually here so we can keep APIView
    (simpler than GenericAPIView for explicit control).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = RecordService.list_records(request.user)

        # Apply filters manually since we're not using GenericAPIView
        filterset = FinancialRecordFilter(request.GET, queryset=qs)
        if not filterset.is_valid():
            return error_response("Invalid filter parameters.", filterset.errors)
        qs = filterset.qs

        # Search by title or notes
        search = request.GET.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        # Ordering
        ordering = request.GET.get("ordering", "-date")
        allowed_orderings = {"date", "-date", "amount", "-amount", "created_at", "-created_at"}
        if ordering in allowed_orderings:
            qs = qs.order_by(ordering)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = FinancialRecordListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = FinancialRecordSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            record = RecordService.create_record(request.user, serializer.validated_data)
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)

        return created_response(
            FinancialRecordSerializer(record).data,
            "Financial record created.",
        )


class FinancialRecordDetailView(APIView):
    """
    GET    /api/v1/finance/records/<id>/  — all roles
    PATCH  /api/v1/finance/records/<id>/  — analyst (own), admin (any)
    DELETE /api/v1/finance/records/<id>/  — admin only (soft delete)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = RecordService.get_record(record_id, request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(FinancialRecordSerializer(record).data)

    def patch(self, request, record_id):
        try:
            record = RecordService.get_record(record_id, request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)

        serializer = FinancialRecordSerializer(
            record, data=request.data, partial=True, context={"request": request}
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            record = RecordService.update_record(record_id, request.user, serializer.validated_data)
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)

        return success_response(FinancialRecordSerializer(record).data, "Record updated.")

    def delete(self, request, record_id):
        try:
            RecordService.delete_record(record_id, request.user)
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(message="Record deleted.")


# ─── Categories ───────────────────────────────────────────────────────────────

class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = CategoryService.list_categories(request.user)
        return success_response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        try:
            category = CategoryService.create_category(request.user, serializer.validated_data)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return created_response(CategorySerializer(category).data, "Category created.")


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = CategoryService.get_category(category_id, request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(CategorySerializer(category).data)

    def patch(self, request, category_id):
        try:
            category = CategoryService.update_category(
                category_id, request.user, request.data
            )
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(CategorySerializer(category).data, "Category updated.")

    def delete(self, request, category_id):
        try:
            CategoryService.delete_category(category_id, request.user)
        except ServiceError as e:
            return error_response(e.message, status_code=e.status_code)
        return success_response(message="Category deleted.")


# ─── Dashboard / Analytics ────────────────────────────────────────────────────

class DashboardSummaryView(APIView):
    """
    GET /api/v1/finance/dashboard/summary/
    Query params: date_from, date_to (YYYY-MM-DD)
    Access: Analyst, Admin
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        try:
            summary = DashboardService.get_summary(request.user, date_from, date_to)
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)
        serializer = DashboardSummarySerializer(summary)
        return success_response(serializer.data)


class CategoryBreakdownView(APIView):
    """
    GET /api/v1/finance/dashboard/categories/
    Query params: date_from, date_to
    Access: Analyst, Admin
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        try:
            breakdown = DashboardService.get_category_breakdown(
                request.user, date_from, date_to
            )
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)
        serializer = CategoryAggregationSerializer(breakdown, many=True)
        return success_response(serializer.data)


class RecentTransactionsView(APIView):
    """
    GET /api/v1/finance/dashboard/recent/
    Query param: limit (default 10, max 50)
    Access: Analyst, Admin
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = min(int(request.GET.get("limit", 10)), 50)
        except (ValueError, TypeError):
            limit = 10

        try:
            records = DashboardService.get_recent_transactions(request.user, limit)
        except (ServiceError, PermissionDeniedError) as e:
            return error_response(e.message, status_code=e.status_code)

        return success_response(FinancialRecordListSerializer(records, many=True).data)
