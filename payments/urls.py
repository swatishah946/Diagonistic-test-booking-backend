from django.urls import path

from .views import PaymentSimulateView, PaymentWebhookView

urlpatterns = [
    path("simulate/", PaymentSimulateView.as_view(), name="payment-simulate"),
    path("webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
]
