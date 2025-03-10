from django.urls import path
from django.contrib.auth.views import LoginView
from .views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    PasswordChangeView,
    PasswordResetView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("login/", LoginView.as_view(), name="login"),
]
