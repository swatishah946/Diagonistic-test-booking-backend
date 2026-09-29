"""
Auth views: signup and login.

Login is delegated to SimpleJWT's TokenObtainPairView with a customized
serializer so descriptive validation errors (e.g. bad credentials) are
returned consistently with the rest of the API.
"""

import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, SignupSerializer, UserSerializer

logger = logging.getLogger(__name__)


class SignupView(generics.CreateAPIView):
    """POST /api/auth/signup/ — register a new user with email + password."""

    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("user_signup_success email=%s user_id=%s", user.email, user.id)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — exchange email + password for a JWT pair."""

    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
