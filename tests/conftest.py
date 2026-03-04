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
def superuser(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123",
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
def expired_access_token(user):
    from datetime import timedelta
    from easyjwt_auth.utils import aware_utcnow

    token = AccessToken.for_user(user)
    token.set_exp(from_time=aware_utcnow() - timedelta(hours=1))
    return str(token)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def user_credentials():
    return {"email": "test@example.com", "password": "testpass123"}
