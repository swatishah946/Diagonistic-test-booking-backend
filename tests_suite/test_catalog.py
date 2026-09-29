"""
Tests for diagnostic centre and test listing endpoints.
"""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from catalog.models import DiagnosticCentre, DiagnosticTest

pytestmark = pytest.mark.django_db


class TestCentreListing:
    def test_list_centres_includes_nested_tests(self, api_client, centre, diagnostic_test):
        url = reverse("centre-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if "results" in response.data else response.data
        assert len(results) == 1
        assert results[0]["name"] == centre.name
        assert len(results[0]["tests"]) == 1
        assert results[0]["tests"][0]["name"] == diagnostic_test.name

    def test_list_centres_does_not_require_auth(self, api_client, centre):
        url = reverse("centre-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_centre_requires_admin(self, auth_client):
        url = reverse("centre-list-create")
        response = auth_client.post(url, {"name": "New Centre", "location": "Jaipur"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_centre(self, admin_client_jwt):
        url = reverse("centre-list-create")
        response = admin_client_jwt.post(url, {"name": "New Centre", "location": "Jaipur"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert DiagnosticCentre.objects.filter(name="New Centre").exists()


class TestTestCreationAndListing:
    def test_admin_can_create_test_under_centre(self, admin_client_jwt, centre):
        url = reverse("centre-test-create", kwargs={"centre_id": centre.id})
        response = admin_client_jwt.post(url, {"name": "Lipid Panel", "price": "899.00"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert DiagnosticTest.objects.filter(centre=centre, name="Lipid Panel").exists()

    def test_non_admin_cannot_create_test(self, auth_client, centre):
        url = reverse("centre-test-create", kwargs={"centre_id": centre.id})
        response = auth_client.post(url, {"name": "Lipid Panel", "price": "899.00"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_test_negative_price_rejected(self, admin_client_jwt, centre):
        url = reverse("centre-test-create", kwargs={"centre_id": centre.id})
        response = admin_client_jwt.post(url, {"name": "Bad Test", "price": "-10.00"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_test_for_nonexistent_centre_404(self, admin_client_jwt):
        url = reverse("centre-test-create", kwargs={"centre_id": 99999})
        response = admin_client_jwt.post(url, {"name": "Lipid Panel", "price": "899.00"}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_all_tests(self, api_client, diagnostic_test):
        url = reverse("test-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"] if "results" in response.data else response.data
        assert any(t["id"] == diagnostic_test.id for t in results)

    def test_list_tests_filter_by_centre(self, api_client, centre, diagnostic_test):
        other_centre = DiagnosticCentre.objects.create(name="Other Centre", location="Delhi")
        DiagnosticTest.objects.create(centre=other_centre, name="X-Ray", price=Decimal("300.00"))

        url = reverse("test-list")
        response = api_client.get(url, {"centre": centre.id})
        results = response.data["results"] if "results" in response.data else response.data
        assert all(t["centre"] == centre.id for t in results)
