"""
PaymentTransaction model — the idempotency ledger for webhook events.

Every processed webhook event is recorded here, keyed on the gateway's
unique `event_id`. Before applying any state change, the webhook task
checks whether that `event_id` has already been recorded; if so, the event
is a duplicate delivery and is a safe no-op.
"""

from django.db import models


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    booking = models.ForeignKey("bookings.Booking", related_name="payment_transactions", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices)
    raw_payload = models.JSONField()
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-processed_at"]

    def __str__(self):
        return f"PaymentTransaction({self.event_id}, {self.status}, booking={self.booking_id})"
