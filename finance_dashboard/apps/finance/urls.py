from django.urls import path
from apps.finance.views import (
    FinancialRecordListCreateView,
    FinancialRecordDetailView,
    CategoryListCreateView,
    CategoryDetailView,
    DashboardSummaryView,
    CategoryBreakdownView,
    RecentTransactionsView,
)

urlpatterns = [
    # Financial Records
    path("records/", FinancialRecordListCreateView.as_view(), name="record-list-create"),
    path("records/<uuid:record_id>/", FinancialRecordDetailView.as_view(), name="record-detail"),

    # Categories
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<uuid:category_id>/", CategoryDetailView.as_view(), name="category-detail"),

    # Dashboard / Analytics
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/categories/", CategoryBreakdownView.as_view(), name="dashboard-categories"),
    path("dashboard/recent/", RecentTransactionsView.as_view(), name="dashboard-recent"),
]
