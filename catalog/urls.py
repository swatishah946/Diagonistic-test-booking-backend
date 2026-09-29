from django.urls import path

from .views import (
    DiagnosticCentreListCreateView,
    DiagnosticTestCreateForCentreView,
    DiagnosticTestListView,
)

urlpatterns = [
    path("centres/", DiagnosticCentreListCreateView.as_view(), name="centre-list-create"),
    path("centres/<int:centre_id>/tests/", DiagnosticTestCreateForCentreView.as_view(), name="centre-test-create"),
    path("tests/", DiagnosticTestListView.as_view(), name="test-list"),
]
