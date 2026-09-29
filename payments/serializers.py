"""
Serializers for the simulated payment endpoint and the payment webhook.
"""

from rest_framework import serializers

from bookings.models import Booking

from .models import PaymentTransaction


class PaymentSimulateSerializer(serializers.Serializer):
    """POST /api/payments/simulate/ request body."""

    booking_id = serializers.UUIDField()
    simulate_status = serializers.ChoiceField(choices=["SUCCESS", "FAILED"])

    def validate_booking_id(self, value):
        try:
            self._booking = Booking.objects.get(pk=value)
        except Booking.DoesNotExist as exc:
            raise serializers.ValidationError("Booking not found.") from exc
        return value

    def get_booking(self):
        return self._booking


class PaymentWebhookSerializer(serializers.Serializer):
    """
    POST /api/payments/webhook/ request body.

    This only validates *shape* (required fields, correct types) — the
    actual idempotency/state-machine logic lives in the Celery task, since
    that logic must run inside a DB transaction with row locking.
    """

    event_id = serializers.CharField(max_length=255)
    booking_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["SUCCESS", "FAILED"])


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ("id", "event_id", "booking", "status", "raw_payload", "processed_at")
        read_only_fields = fields
