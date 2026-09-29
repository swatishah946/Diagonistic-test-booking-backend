"""
Serializers for signup and JWT login.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user account.

    Password strength is enforced via Django's configured password
    validators, and duplicate emails are rejected with a descriptive error
    rather than a generic IntegrityError / 500.
    """

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "email", "password", "full_name")
        read_only_fields = ("id",)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "date_joined")
        read_only_fields = fields


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Standard SimpleJWT pair serializer. The USERNAME_FIELD on the custom
    User model is already "email", so the default `username` field
    SimpleJWT exposes on the serializer transparently maps to email.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token
