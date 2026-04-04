"""
core/models.py

Base abstract model used across all apps.

Design decisions:
- SoftDeleteManager excludes deleted records by default so all queries
  automatically respect soft delete without needing `.filter(is_deleted=False)`.
- `all_objects` manager is provided for admin/audit access.
- Timestamps (created_at, updated_at) are auto-managed.
"""

import uuid
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Default manager — only returns non-deleted records."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Abstract base model providing:
    - UUID primary key (avoids enumeration attacks)
    - created_at / updated_at timestamps
    - Soft delete via is_deleted + deleted_at
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Default manager respects soft delete
    objects = SoftDeleteManager()
    # Bypass soft delete for admin/internal use
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark record as deleted without removing from DB."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

    def restore(self):
        """Undo a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
