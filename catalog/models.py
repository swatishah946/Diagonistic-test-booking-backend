"""
Catalog models: DiagnosticCentre and DiagnosticTest.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class DiagnosticCentre(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location})"


class DiagnosticTest(models.Model):
    centre = models.ForeignKey(DiagnosticCentre, related_name="tests", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    # Prices are never negative — enforced at both the model and serializer level.
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} @ {self.centre.name} (₹{self.price})"
