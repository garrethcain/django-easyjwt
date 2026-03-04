import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTokenObtainPairView:
    def test_post_valid_credentials_returns_tokens(self, api_client, user, user_credentials):
        url = reverse("token_obtain_pair")

        response = api_client.post(url, user_credentials, format="json")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_post_invalid_credentials_returns_401(self, api_client):
        url = reverse("token_obtain_pair")
        invalid_credentials = {"email": "wrong@example.com", "password": "wrongpass"}

        response = api_client.post(url, invalid_credentials, format="json")

        assert response.status_code == 401

    def test_post_inactive_user_returns_401(self, api_client, inactive_user):
        url = reverse("token_obtain_pair")
        credentials = {"email": "inactive@example.com", "password": "testpass123"}

        response = api_client.post(url, credentials, format="json")

        assert response.status_code == 401

    def test_post_missing_credentials_returns_400(self, api_client):
        url = reverse("token_obtain_pair")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestTokenRefreshView:
    def test_post_valid_refresh_token_returns_access(self, api_client, refresh_token):
        url = reverse("token_refresh")

        response = api_client.post(url, {"refresh": refresh_token}, format="json")

        assert response.status_code == 200
        assert "access" in response.data

    def test_post_invalid_refresh_token_returns_401(self, api_client):
        url = reverse("token_refresh")

        response = api_client.post(url, {"refresh": "invalid.token"}, format="json")

        assert response.status_code == 401

    def test_post_access_token_as_refresh_returns_401(self, api_client, access_token):
        url = reverse("token_refresh")

        response = api_client.post(url, {"refresh": access_token}, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenVerifyView:
    def test_post_valid_token_returns_200(self, api_client, access_token):
        url = reverse("token_verify")

        response = api_client.post(url, {"token": access_token}, format="json")

        assert response.status_code == 200

    def test_post_invalid_token_returns_401(self, api_client):
        url = reverse("token_verify")

        response = api_client.post(url, {"token": "invalid.token"}, format="json")

        assert response.status_code == 401

    def test_post_missing_token_returns_400(self, api_client):
        url = reverse("token_verify")

        response = api_client.post(url, {}, format="json")

        assert response.status_code == 400
