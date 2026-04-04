from django.contrib import admin
from apps.finance.models import Category, FinancialRecord


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at", "is_deleted"]
    list_filter = ["is_deleted"]
    search_fields = ["name", "owner__email"]


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ["title", "transaction_type", "amount", "date", "owner", "is_deleted"]
    list_filter = ["transaction_type", "is_deleted", "date"]
    search_fields = ["title", "owner__email"]
    date_hierarchy = "date"
