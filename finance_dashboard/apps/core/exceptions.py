"""
core/exceptions.py

Centralised exception handling.

Why a custom handler?
DRF's default handler returns inconsistent shapes (sometimes 'detail', sometimes
field-level errors). This wrapper normalises ALL error responses to:
  { "error": true, "message": "...", "errors": {...} }

This makes it trivial for a frontend to handle errors uniformly.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """Wrap DRF's default handler output in a consistent envelope."""
    response = exception_handler(exc, context)

    if response is not None:
        # Flatten DRF's error dict into our envelope
        errors = response.data
        message = _extract_message(errors)
        response.data = {
            "error": True,
            "message": message,
            "errors": errors,
        }

    return response


def _extract_message(errors):
    """Pull a human-readable top-level message from DRF's error structure."""
    if isinstance(errors, dict):
        if "detail" in errors:
            return str(errors["detail"])
        # Return first field's first error as the top-level message
        for key, value in errors.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            if isinstance(value, str):
                return f"{key}: {value}"
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return "An error occurred."


class ServiceError(Exception):
    """
    Raised by the service layer for business-logic violations.
    Views catch this and return a 400 response.
    Keeps business logic errors distinct from Django/DRF exceptions.
    """

    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class PermissionDeniedError(ServiceError):
    """Raised when a user attempts an action beyond their role."""

    def __init__(self, message="You do not have permission to perform this action."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)
