from django.urls import path
from django.contrib.auth.views import LoginView
from .views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
    CreateUserView,
    PasswordChangeView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("create-user/", CreateUserView.as_view(), name="create_user"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("login/", LoginView.as_view(), name="login"),
]
