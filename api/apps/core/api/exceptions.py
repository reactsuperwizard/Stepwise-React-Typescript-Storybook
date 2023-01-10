from typing import Optional

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as base_exception_handler


def exception_handler(exception: Exception, context: dict) -> Optional[Response]:
    if isinstance(exception, DjangoValidationError):
        exception = exceptions.ValidationError(as_serializer_error(exception))

    if isinstance(exception, Http404):
        exception = exceptions.NotFound()

    if isinstance(exception, PermissionDenied):
        exception = exceptions.PermissionDenied()

    response = base_exception_handler(exception, context)

    # If unexpected error occurs (server error, etc.)
    if response is None:
        return response

    exception_detail = getattr(exception, "detail", None)

    if isinstance(exception_detail, (list, dict)):
        response.data = {"detail": response.data}

    return response
