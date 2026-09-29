"""
Payment views: simulated (synchronous) payment and asynchronous webhook.
"""

import logging

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from bookings.models import Booking

from .serializers import PaymentSimulateSerializer, PaymentWebhookSerializer
from .tasks import process_webhook_task

logger = logging.getLogger("payments")


class PaymentSimulateView(APIView):
    """
    POST /api/payments/simulate/

    Synchronously flips a PENDING booking to CONFIRMED or FAILED, as if a
    payment gateway had just responded inline. Only the booking's owner may
    simulate a payment for it, and only while the booking is still PENDING.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PaymentSimulateSerializer, responses={200: dict, 409: dict})
    def post(self, request, *args, **kwargs):
        serializer = PaymentSimulateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking_id = serializer.validated_data["booking_id"]
        simulate_status = serializer.validated_data["simulate_status"]

        with transaction.atomic():
            try:
                booking = Booking.objects.select_for_update().get(pk=booking_id)
            except Booking.DoesNotExist:
                raise ValidationError({"booking_id": "Booking not found."})

            if booking.user_id != request.user.id:
                raise PermissionDenied("You do not have permission to act on this booking.")

            if booking.status != Booking.Status.PENDING:
                return Response(
                    {
                        "detail": (
                            f"Cannot simulate payment: booking is in '{booking.status}' state, "
                            "not 'PENDING'."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            booking.status = Booking.Status.CONFIRMED if simulate_status == "SUCCESS" else Booking.Status.FAILED
            booking.save(update_fields=["status", "updated_at"])

            logger.info(
                "payment_simulated booking_id=%s user_id=%s result=%s new_status=%s",
                booking.id, request.user.id, simulate_status, booking.status,
            )

        return Response(
            {"booking_id": str(booking.id), "status": booking.status},
            status=status.HTTP_200_OK,
        )


class PaymentWebhookView(APIView):
    """
    POST /api/payments/webhook/

    Validates the incoming payload's shape only, then hands off to a Celery
    task for the actual idempotent, concurrency-safe processing, and
    returns immediately. No authentication is required here since real
    payment gateways call this endpoint directly (in production this would
    instead be protected by HMAC-SHA256 signature verification — see
    README "Future Improvements").
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "webhook"

    @extend_schema(request=PaymentWebhookSerializer, responses={202: dict})
    def post(self, request, *args, **kwargs):
        serializer = PaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        # UUIDField parses to a UUID object; make the payload JSON-serializable
        # before handing it to Celery.
        payload = {**payload, "booking_id": str(payload["booking_id"])}

        process_webhook_task.delay(payload)

        logger.info("webhook_received_enqueued event_id=%s booking_id=%s", payload["event_id"], payload["booking_id"])

        return Response({"detail": "Webhook accepted for processing."}, status=status.HTTP_202_ACCEPTED)
