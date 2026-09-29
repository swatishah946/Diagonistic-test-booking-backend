"""
Booking serializers.

Key rule: `amount` is never accepted from the client. It is always derived
server-side from `test.price` at creation time (a price snapshot), so later
price changes on the DiagnosticTest don't retroactively affect existing
bookings, and clients cannot manipulate the amount they're charged.
"""

from django.utils import timezone
from rest_framework import serializers

from catalog.models import DiagnosticTest

from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    test = serializers.PrimaryKeyRelatedField(queryset=DiagnosticTest.objects.select_related("centre").all())

    class Meta:
        model = Booking
        fields = ("id", "test", "appointment_time", "amount", "status", "centre", "created_at")
        read_only_fields = ("id", "amount", "status", "centre", "created_at")

    def validate_appointment_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment time must be in the future.")
        return value

    def create(self, validated_data):
        test = validated_data.pop("test")
        request = self.context["request"]
        booking = Booking.objects.create(
            user=request.user,
            test=test,
            centre=test.centre,
            amount=test.price,  # server-side snapshot — client input is ignored
            **validated_data,
        )
        return booking


class BookingSerializer(serializers.ModelSerializer):
    """Used for retrieve/list — read-only, fully expanded view of a booking."""

    test_name = serializers.CharField(source="test.name", read_only=True)
    centre_name = serializers.CharField(source="centre.name", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id",
            "user",
            "centre",
            "centre_name",
            "test",
            "test_name",
            "appointment_time",
            "amount",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
