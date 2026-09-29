"""
Tests for signup and JWT login.
"""

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


class TestSignup:
    def test_signup_success(self, api_client):
        url = reverse("auth-signup")
        response = api_client.post(
            url,
            {"email": "newuser@example.com", "password": "StrongPass123", "full_name": "New User"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newuser@example.com"
        assert "password" not in response.data

    def test_signup_duplicate_email_rejected(self, api_client, user):
        url = reverse("auth-signup")
        response = api_client.post(
            url, {"email": user.email, "password": "StrongPass123"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data

    def test_signup_missing_fields(self, api_client):
        url = reverse("auth-signup")
        response = api_client.post(url, {"email": "incomplete@example.com"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup_weak_password_rejected(self, api_client):
        url = reverse("auth-signup")
        response = api_client.post(
            url, {"email": "weak@example.com", "password": "123"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    def test_login_success_returns_jwt_pair(self, api_client, user):
        url = reverse("auth-login")
        response = api_client.post(
            url, {"email": user.email, "password": "StrongPass123"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password_rejected(self, api_client, user):
        url = reverse("auth-login")
        response = api_client.post(
            url, {"email": user.email, "password": "WrongPassword"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_requires_token(self, api_client):
        url = reverse("booking-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_rejects_malformed_token(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        url = reverse("booking-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
