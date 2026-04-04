"""
finance/filters.py

django-filter FilterSet for FinancialRecord.

Separating filter logic from views keeps view code clean and
makes filters independently testable.
"""

import django_filters
from apps.finance.models import FinancialRecord


class FinancialRecordFilter(django_filters.FilterSet):
    # Date range filtering — common for finance dashboards
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = FinancialRecord
        fields = ["transaction_type", "category", "date_from", "date_to", "min_amount", "max_amount"]
