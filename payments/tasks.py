"""
Celery task(s) for asynchronous, idempotent webhook processing.

Design notes
------------
1. **Idempotency**: `PaymentTransaction.event_id` is unique. Before touching
   booking state we check whether this `event_id` has already been
   recorded. If so, we exit without modifying anything — this guarantees
   that redelivered webhook events (a normal occurrence with real payment
   gateways) never double-apply a state change or create duplicate ledger
   rows.

2. **Concurrency safety**: The booking row is locked with
   `select_for_update()` inside an atomic transaction for the whole
   read-check-write sequence, so two webhook deliveries (or a webhook and a
   /payments/simulate/ call) racing on the same booking cannot both "win".

3. **Terminal state protection**: Once a booking reaches a terminal state
   (`CONFIRMED` or `CANCELLED`), no further webhook may change it — in
   particular, an out-of-order `FAILED` arriving after a `CONFIRMED` is
   safely ignored rather than corrupting a completed booking.

4. **Resilience**: The task retries on transient failures (e.g. a DB
   deadlock) with exponential backoff, capped at 3 retries, and is
   rate-limited to avoid overwhelming the database during a burst of
   redelivered events.
"""

import logging

from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import DatabaseError, transaction

logger = get_task_logger(__name__)
django_logger = logging.getLogger("payments")


@shared_task(
    bind=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    rate_limit="50/m",
    autoretry_for=(DatabaseError,),
)
def process_webhook_task(self, payload: dict):
    """
    Process a single payment-webhook payload.

    `payload` is the already-schema-validated dict:
        {"event_id": str, "booking_id": str(uuid), "status": "SUCCESS"|"FAILED"}
    """
    # Imported lazily inside the task to avoid app-registry-not-ready issues
    # when Celery workers boot before Django apps are fully loaded.
    from bookings.models import Booking
    from payments.models import PaymentTransaction

    event_id = payload["event_id"]
    booking_id = payload["booking_id"]
    incoming_status = payload["status"]

    # NOTE: `autoretry_for=(DatabaseError,)` on the task decorator already
    # handles retry-with-backoff for transient DB errors (e.g. deadlocks
    # under select_for_update contention), so we let those propagate rather
    # than catching them here — no manual `self.retry()` needed.
    with transaction.atomic():
        # Idempotency check — first line of defense, cheap and race-safe
        # because event_id has a unique DB constraint: even if two
        # workers somehow race past this check, the second INSERT below
        # will hit an IntegrityError instead of double-applying state.
        if PaymentTransaction.objects.filter(event_id=event_id).exists():
            django_logger.info(
                "webhook_duplicate_ignored event_id=%s booking_id=%s", event_id, booking_id
            )
            return {"status": "duplicate_ignored", "event_id": event_id}

        # Lock the booking row for the remainder of this transaction so
        # no concurrent webhook/simulate call can interleave with the
        # state check + transition below.
        try:
            booking = Booking.objects.select_for_update().get(pk=booking_id)
        except Booking.DoesNotExist:
            django_logger.warning(
                "webhook_booking_not_found event_id=%s booking_id=%s", event_id, booking_id
            )
            # Still record the transaction attempt for audit purposes,
            # tagged against no valid booking is not possible (FK is
            # required) — so we simply drop it. In a real system this
            # would go to a dead-letter queue for investigation.
            return {"status": "booking_not_found", "event_id": event_id}

        # Terminal-state protection: once CONFIRMED or CANCELLED, no
        # further webhook (including an out-of-order FAILED) may alter
        # the booking's status.
        if booking.is_terminal():
            django_logger.info(
                "webhook_ignored_terminal_state event_id=%s booking_id=%s "
                "current_status=%s incoming_status=%s",
                event_id, booking_id, booking.status, incoming_status,
            )
            PaymentTransaction.objects.create(
                event_id=event_id,
                booking=booking,
                status=incoming_status,
                raw_payload=payload,
            )
            return {"status": "ignored_terminal_state", "event_id": event_id}

        new_status = Booking.Status.CONFIRMED if incoming_status == "SUCCESS" else Booking.Status.FAILED
        booking.status = new_status
        booking.save(update_fields=["status", "updated_at"])

        PaymentTransaction.objects.create(
            event_id=event_id,
            booking=booking,
            status=incoming_status,
            raw_payload=payload,
        )

        django_logger.info(
            "webhook_processed event_id=%s booking_id=%s new_status=%s",
            event_id, booking_id, new_status,
        )
        return {"status": "processed", "event_id": event_id, "booking_status": new_status}
