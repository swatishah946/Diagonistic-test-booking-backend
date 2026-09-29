"""
Views for diagnostic centres and tests.

Read endpoints (listing centres/tests) are open to any client so users can
browse the catalog before authenticating; write endpoints (creating a
centre or a test under a centre) are restricted to admin/staff users.
"""

import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.exceptions import NotFound

from .models import DiagnosticCentre, DiagnosticTest
from .serializers import (
    DiagnosticCentreSerializer,
    DiagnosticTestCreateSerializer,
    DiagnosticTestSerializer,
)

logger = logging.getLogger(__name__)


class DiagnosticCentreListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/centres/ — list all centres with their nested tests.
    POST /api/centres/ — create a new centre (admin/staff only).
    """

    queryset = DiagnosticCentre.objects.prefetch_related("tests").all()
    serializer_class = DiagnosticCentreSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        centre = serializer.save()
        logger.info("centre_created id=%s name=%s", centre.id, centre.name)


class DiagnosticTestCreateForCentreView(generics.CreateAPIView):
    """POST /api/centres/<id>/tests/ — create a test under a specific centre."""

    serializer_class = DiagnosticTestCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_centre(self):
        centre_id = self.kwargs["centre_id"]
        try:
            return DiagnosticCentre.objects.get(pk=centre_id)
        except DiagnosticCentre.DoesNotExist as exc:
            raise NotFound(f"Diagnostic centre {centre_id} not found.") from exc

    def perform_create(self, serializer):
        centre = self.get_centre()
        test = serializer.save(centre=centre)
        logger.info("test_created id=%s centre_id=%s name=%s", test.id, centre.id, test.name)


class DiagnosticTestListView(generics.ListAPIView):
    """GET /api/tests/ — list all tests, filterable by centre and paginated."""

    queryset = DiagnosticTest.objects.select_related("centre").all()
    serializer_class = DiagnosticTestSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["centre", "centre__location"]
    search_fields = ["name", "centre__name"]
    ordering_fields = ["price", "created_at", "name"]
