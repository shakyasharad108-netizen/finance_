"""
core/responses.py

Thin helpers that produce consistently shaped API responses.

Using these helpers ensures every endpoint returns the same envelope:
  { "error": false, "message": "...", "data": ... }

This makes frontend integration and testing straightforward.
"""

from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    return Response(
        {"error": False, "message": message, "data": data},
        status=status_code,
    )


def created_response(data=None, message="Created successfully"):
    return success_response(data, message, status.HTTP_201_CREATED)


def error_response(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"error": True, "message": message, "errors": errors or {}},
        status=status_code,
    )
