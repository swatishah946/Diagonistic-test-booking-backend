"""
Booking model.

`amount` is always a server-side snapshot of the DiagnosticTest price at the
moment the booking is created — the client's input for price/amount is
never trusted (see bookings/serializers.py).
"""

import uuid

from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    # Terminal states from which no further state transition may occur.
    TERMINAL_STATES = (Status.CONFIRMED, Status.CANCELLED)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bookings", on_delete=models.CASCADE)
    centre = models.ForeignKey("catalog.DiagnosticCentre", related_name="bookings", on_delete=models.PROTECT)
    test = models.ForeignKey("catalog.DiagnosticTest", related_name="bookings", on_delete=models.PROTECT)
    appointment_time = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Booking {self.id} — {self.test.name} for {self.user.email} [{self.status}]"

    def is_terminal(self):
        return self.status in self.TERMINAL_STATES
