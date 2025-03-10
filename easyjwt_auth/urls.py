from django.urls import path
from django.contrib.auth.views import LoginView
from .views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    CreateUserView,
    PasswordChangeView,
)


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("create-user/", CreateUserView.as_view(), name="create_user"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("login/", LoginView.as_view(), name="login"),
]
