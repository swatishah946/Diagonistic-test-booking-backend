"""
Tests for the simulated payment endpoint and the idempotent payment webhook.

`CELERY_TASK_ALWAYS_EAGER` is forced on via the `settings` fixture so that
`process_webhook_task.delay(...)` executes synchronously in-process during
tests, without requiring a running Redis broker or Celery worker.
"""

import uuid

import pytest
from django.urls import reverse
from rest_framework import status

from bookings.models import Booking
from payments.models import PaymentTransaction
from payments.tasks import process_webhook_task

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _eager_celery(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


class TestPaymentSimulate:
    def test_simulate_success_confirms_booking(self, auth_client, booking):
        url = reverse("payment-simulate")
        response = auth_client.post(
            url, {"booking_id": str(booking.id), "simulate_status": "SUCCESS"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

    def test_simulate_failed_fails_booking(self, auth_client, booking):
        url = reverse("payment-simulate")
        response = auth_client.post(
            url, {"booking_id": str(booking.id), "simulate_status": "FAILED"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        booking.refresh_from_db()
        assert booking.status == Booking.Status.FAILED

    def test_simulate_rejects_non_pending_booking(self, auth_client, booking):
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status"])

        url = reverse("payment-simulate")
        response = auth_client.post(
            url, {"booking_id": str(booking.id), "simulate_status": "SUCCESS"}, format="json"
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED  # unchanged

    def test_simulate_nonexistent_booking_400(self, auth_client):
        url = reverse("payment-simulate")
        response = auth_client.post(
            url, {"booking_id": str(uuid.uuid4()), "simulate_status": "SUCCESS"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_simulate_other_users_booking_forbidden(self, other_auth_client, booking):
        url = reverse("payment-simulate")
        response = other_auth_client.post(
            url, {"booking_id": str(booking.id), "simulate_status": "SUCCESS"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWebhookIdempotency:
    def test_webhook_confirms_pending_booking(self, api_client, booking):
        url = reverse("payment-webhook")
        payload = {"event_id": "evt_001", "booking_id": str(booking.id), "status": "SUCCESS"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_202_ACCEPTED

        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED
        assert PaymentTransaction.objects.filter(event_id="evt_001").count() == 1

    def test_duplicate_webhook_event_id_is_noop(self, api_client, booking):
        """Sending the same event_id twice must not create a duplicate PaymentTransaction
        or change booking state twice."""
        url = reverse("payment-webhook")
        payload = {"event_id": "evt_dup_001", "booking_id": str(booking.id), "status": "SUCCESS"}

        response1 = api_client.post(url, payload, format="json")
        assert response1.status_code == status.HTTP_202_ACCEPTED
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

        # Resend the identical event
        response2 = api_client.post(url, payload, format="json")
        assert response2.status_code == status.HTTP_202_ACCEPTED

        assert PaymentTransaction.objects.filter(event_id="evt_dup_001").count() == 1
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED  # unchanged, not double-processed

    def test_out_of_order_failed_after_confirmed_is_ignored(self, booking):
        """A FAILED event arriving after the booking is already CONFIRMED must not
        regress the booking's terminal state."""
        # First: confirm the booking directly via the task
        process_webhook_task(
            {"event_id": "evt_success_1", "booking_id": str(booking.id), "status": "SUCCESS"}
        )
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED

        # Then: an out-of-order FAILED event with a *different* event_id arrives
        process_webhook_task(
            {"event_id": "evt_failed_late", "booking_id": str(booking.id), "status": "FAILED"}
        )
        booking.refresh_from_db()
        assert booking.status == Booking.Status.CONFIRMED  # still confirmed, not regressed

        # The late event is still recorded in the ledger (for audit), just without effect
        txn = PaymentTransaction.objects.get(event_id="evt_failed_late")
        assert txn.status == "FAILED"

    def test_webhook_for_nonexistent_booking_does_not_crash(self, api_client):
        url = reverse("payment-webhook")
        payload = {"event_id": "evt_ghost", "booking_id": str(uuid.uuid4()), "status": "SUCCESS"}
        response = api_client.post(url, payload, format="json")
        # Schema is valid, so the webhook is still accepted; the task itself
        # safely no-ops when the referenced booking doesn't exist.
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert not PaymentTransaction.objects.filter(event_id="evt_ghost").exists()

    def test_webhook_missing_fields_rejected(self, api_client):
        url = reverse("payment-webhook")
        response = api_client.post(url, {"event_id": "evt_bad"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_webhook_does_not_require_auth(self, api_client, booking):
        """Payment gateways call the webhook directly without a user JWT."""
        url = reverse("payment-webhook")
        payload = {"event_id": "evt_no_auth", "booking_id": str(booking.id), "status": "SUCCESS"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_202_ACCEPTED


class TestRateLimiting:
    def test_login_endpoint_is_throttled_for_anonymous_bursts(self, api_client, user, monkeypatch):
        """Anonymous requests (e.g. brute-forced logins) get throttled past
        the configured per-minute rate.

        DRF resolves `AnonRateThrottle`'s rate from a class attribute set at
        import time, so we patch it directly (and clear the throttle cache)
        rather than relying on a live settings override to propagate.
        """
        from django.core.cache import cache
        from rest_framework.throttling import AnonRateThrottle

        cache.clear()
        monkeypatch.setitem(AnonRateThrottle.THROTTLE_RATES, "anon", "2/minute")

        url = reverse("auth-login")
        body = {"email": user.email, "password": "WrongPassword"}

        for _ in range(2):
            response = api_client.post(url, body, format="json")
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

        throttled = api_client.post(url, body, format="json")
        assert throttled.status_code == status.HTTP_429_TOO_MANY_REQUESTS
