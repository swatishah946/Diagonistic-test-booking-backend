"""
Shared pytest fixtures for the test suite.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from catalog.models import DiagnosticCentre, DiagnosticTest

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(email="patient@example.com", password="StrongPass123")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(email="other@example.com", password="StrongPass123")


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(email="admin@example.com", password="AdminPass123")


@pytest.fixture
def auth_client(user):
    # Uses its own APIClient instance (rather than the shared `api_client`
    # fixture) so that authenticating this client never bleeds into
    # `other_auth_client` / `admin_client_jwt` used in the same test.
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_auth_client(other_user):
    client = APIClient()
    client.force_authenticate(user=other_user)
    return client


@pytest.fixture
def admin_client_jwt(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def centre():
    return DiagnosticCentre.objects.create(name="City Diagnostics", location="Kota")


@pytest.fixture
def diagnostic_test(centre):
    return DiagnosticTest.objects.create(centre=centre, name="Complete Blood Count", price=Decimal("499.00"))


@pytest.fixture
def booking(user, centre, diagnostic_test):
    return Booking.objects.create(
        user=user,
        centre=centre,
        test=diagnostic_test,
        appointment_time=timezone.now() + timedelta(days=1),
        amount=diagnostic_test.price,
        status=Booking.Status.PENDING,
    )
