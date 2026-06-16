import pytest
from rest_framework.test import APIClient

from easyjwt_auth.tokens import AccessToken, RefreshToken
from easyjwt_user.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def inactive_user(db):
    return User.objects.create_user(
        email="inactive@example.com",
        password="testpass123",
        first_name="Inactive",
        last_name="User",
        is_active=False,
    )


@pytest.fixture
def access_token(user):
    token = AccessToken.for_user(user)
    return str(token)


@pytest.fixture
def refresh_token(user):
    token = RefreshToken.for_user(user)
    return str(token)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_credentials():
    return {"email": "test@example.com", "password": "testpass123"}
