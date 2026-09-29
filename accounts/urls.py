from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, SignupView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="auth-signup"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
]
