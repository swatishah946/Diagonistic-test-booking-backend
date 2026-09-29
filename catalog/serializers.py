"""
Serializers for diagnostic centres and tests.
"""

from rest_framework import serializers

from .models import DiagnosticCentre, DiagnosticTest


class DiagnosticTestSerializer(serializers.ModelSerializer):
    centre_name = serializers.CharField(source="centre.name", read_only=True)

    class Meta:
        model = DiagnosticTest
        fields = ("id", "centre", "centre_name", "name", "price", "created_at")
        read_only_fields = ("id", "created_at", "centre_name")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive value.")
        return value


class DiagnosticTestNestedSerializer(serializers.ModelSerializer):
    """Used to embed tests inside a centre's payload without exposing `centre` again."""

    class Meta:
        model = DiagnosticTest
        fields = ("id", "name", "price", "created_at")
        read_only_fields = fields


class DiagnosticTestCreateSerializer(serializers.ModelSerializer):
    """Used for POST /api/centres/<id>/tests/ — centre is set from the URL, not the body."""

    class Meta:
        model = DiagnosticTest
        fields = ("id", "name", "price", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive value.")
        return value


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    tests = DiagnosticTestNestedSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticCentre
        fields = ("id", "name", "location", "created_at", "tests")
        read_only_fields = ("id", "created_at", "tests")
