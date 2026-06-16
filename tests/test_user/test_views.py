import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client_urls(settings):
    settings.ROOT_URLCONF = "tests.test_client.urls"


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenUserDetailView:
    def test_authenticated_user_gets_profile(self, access_token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get("/auth/user/")

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    def test_unauthenticated_request_rejected(self):
        """SEC-3: unauthenticated requests should be rejected with 401 or 403."""
        client = APIClient()
        response = client.get("/auth/user/")

        assert response.status_code in (401, 403)
