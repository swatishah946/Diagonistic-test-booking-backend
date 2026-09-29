"""
Custom DRF exception handler.

Wraps DRF's default handler to guarantee a consistent, descriptive error
envelope across the API: ``{"detail": <message>, "errors": <field errors>}``.
This keeps 400/401/403/404/422-style responses predictable for API
consumers instead of DRF's default shape varying by exception type.
"""

from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        # Already a simple {"detail": ...} shape (e.g. NotFound, PermissionDenied)
        response.data = {"detail": data["detail"]}
    else:
        # Field validation errors: keep them under "errors", add a generic "detail"
        response.data = {
            "detail": "Request validation failed.",
            "errors": data,
        }
    return response
