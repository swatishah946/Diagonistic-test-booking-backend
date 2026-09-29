"""
Booking views.

Authorization rule (IDOR protection): a booking that exists but belongs to
another user must return 403 Forbidden, not 404 — the spec explicitly
distinguishes "doesn't exist" (404) from "exists but not yours" (403).
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer

logger = logging.getLogger(__name__)


class BookingListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/bookings/ — list bookings for the authenticated user only.
    POST /api/bookings/ — create a booking for the authenticated user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Booking.objects.none()
        return Booking.objects.filter(user=self.request.user).select_related("test", "centre")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        logger.info(
            "booking_created id=%s user_id=%s test_id=%s amount=%s",
            booking.id, request.user.id, booking.test_id, booking.amount,
        )
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(generics.RetrieveAPIView):
    """GET /api/bookings/<id>/ — retrieve a single booking, strictly scoped to its owner."""

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.select_related("test", "centre", "user").all()
    lookup_field = "pk"

    def get_object(self):
        try:
            booking = Booking.objects.select_related("test", "centre", "user").get(pk=self.kwargs["pk"])
        except (Booking.DoesNotExist, ValueError, TypeError) as exc:
            raise NotFound("Booking not found.") from exc

        if booking.user_id != self.request.user.id:
            logger.warning(
                "booking_idor_attempt booking_id=%s owner_id=%s requester_id=%s",
                booking.id, booking.user_id, self.request.user.id,
            )
            raise PermissionDenied("You do not have permission to view this booking.")

        return booking
