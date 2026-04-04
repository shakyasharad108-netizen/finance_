"""
finance/models.py

Two models:
  Category  — user-defined labels (e.g. "Salary", "Groceries")
  FinancialRecord — an individual income or expense transaction

Design decisions:
- Both inherit BaseModel for UUID PK, timestamps, and soft delete.
- TransactionType is a simple TextChoices; new types can be added later.
- `owner` FK links records to the creating user for data isolation —
  Viewers/Analysts only see their own records unless they're Admins.
- `category` is nullable so records can exist before being categorised.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class TransactionType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class Category(BaseModel):
    """
    User-defined transaction category.
    Each user owns their own set of categories.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )

    class Meta:
        db_table = "finance_categories"
        # Prevent duplicate category names per user
        unique_together = [("name", "owner")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.owner.email})"


class FinancialRecord(BaseModel):
    """
    A single financial transaction (income or expense).

    Key fields:
    - transaction_type: income | expense
    - amount: positive decimal; direction determined by transaction_type
    - date: the actual transaction date (not created_at)
    - category: optional grouping
    - notes: free-text annotation
    """

    title = models.CharField(max_length=255)
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        # Amount is always positive; sign implied by transaction_type
    )
    date = models.DateField(db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="records",
    )
    notes = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="financial_records",
    )

    class Meta:
        db_table = "finance_records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "transaction_type"]),
            models.Index(fields=["owner", "date"]),
        ]

    def __str__(self):
        return f"{self.transaction_type.upper()} | {self.title} | {self.amount}"
