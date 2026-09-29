"""
Tests for booking creation, price snapshotting, validation, and IDOR protection.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from bookings.models import Booking

pytestmark = pytest.mark.django_db


class TestBookingCreate:
    def test_create_booking_success(self, auth_client, diagnostic_test):
        url = reverse("booking-list-create")
        appointment_time = (timezone.now() + timedelta(days=2)).isoformat()
        response = auth_client.post(
            url, {"test": diagnostic_test.id, "appointment_time": appointment_time}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == Booking.Status.PENDING
        assert Decimal(response.data["amount"]) == diagnostic_test.price

    def test_amount_is_server_side_snapshot_not_trusted_from_client(self, auth_client, diagnostic_test):
        """Even if the client sends a bogus `amount`, it must be ignored."""
        url = reverse("booking-list-create")
        appointment_time = (timezone.now() + timedelta(days=2)).isoformat()
        response = auth_client.post(
            url,
            {"test": diagnostic_test.id, "appointment_time": appointment_time, "amount": "0.01"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data["amount"]) == diagnostic_test.price

    def test_create_booking_past_appointment_rejected(self, auth_client, diagnostic_test):
        url = reverse("booking-list-create")
        past_time = (timezone.now() - timedelta(days=1)).isoformat()
        response = auth_client.post(
            url, {"test": diagnostic_test.id, "appointment_time": past_time}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_booking_requires_auth(self, api_client, diagnostic_test):
        url = reverse("booking-list-create")
        appointment_time = (timezone.now() + timedelta(days=2)).isoformat()
        response = api_client.post(
            url, {"test": diagnostic_test.id, "appointment_time": appointment_time}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_booking_nonexistent_test_400(self, auth_client):
        url = reverse("booking-list-create")
        appointment_time = (timezone.now() + timedelta(days=2)).isoformat()
        response = auth_client.post(
            url, {"test": 999999, "appointment_time": appointment_time}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestBookingListAndRetrieve:
    def test_list_bookings_scoped_to_user(self, auth_client, other_auth_client, booking):
        url = reverse("booking-list-create")

        response = auth_client.get(url)
        results = response.data["results"] if "results" in response.data else response.data
        assert len(results) == 1

        response = other_auth_client.get(url)
        results = response.data["results"] if "results" in response.data else response.data
        assert len(results) == 0

    def test_retrieve_own_booking_success(self, auth_client, booking):
        url = reverse("booking-detail", kwargs={"pk": booking.id})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(booking.id)

    def test_retrieve_other_users_booking_forbidden(self, other_auth_client, booking):
        """IDOR protection: booking exists but belongs to someone else -> 403, not 404."""
        url = reverse("booking-detail", kwargs={"pk": booking.id})
        response = other_auth_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_nonexistent_booking_404(self, auth_client):
        import uuid

        url = reverse("booking-detail", kwargs={"pk": uuid.uuid4()})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
