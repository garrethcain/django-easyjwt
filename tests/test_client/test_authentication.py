import pytest
from unittest.mock import MagicMock
import responses as responses_mock

from rest_framework import exceptions
from easyjwt_client.authentication import EasyJWTAuthentication, ModelBackend


@pytest.mark.django_db
class TestEasyJWTAuthentication:
    def test_authenticate_valid_remote_token(self, user, access_token):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={},
                status=200,
            )
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                json={
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=200,
            )

            auth = EasyJWTAuthentication()
            request = MagicMock()
            request.META = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
            request.headers = {"Authorization": f"Bearer {access_token}"}

            result = auth.authenticate(request)

            assert result is not None
            authenticated_user, _ = result
            assert authenticated_user.email == user.email

    def test_authenticate_no_header_returns_none(self):
        auth = EasyJWTAuthentication()
        request = MagicMock()
        request.META = {}
        request.headers = {}

        result = auth.authenticate(request)

        assert result is None

    def test_authenticate_malformed_header_raises(self):
        auth = EasyJWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": "BearerOnly"}
        request.headers = {"Authorization": "BearerOnly"}

        with pytest.raises(exceptions.AuthenticationFailed, match="No credentials provided"):
            auth.authenticate(request)

    def test_authenticate_bearer_space_parsing(self, user, access_token):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={},
                status=200,
            )
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                json={
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=200,
            )

            auth = EasyJWTAuthentication()
            request = MagicMock()
            request.META = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
            request.headers = {"Authorization": f"Bearer {access_token}"}

            result = auth.authenticate(request)

            assert result is not None

    def test_authenticate_remote_failure_raises(self, access_token):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={"detail": "Token is invalid"},
                status=401,
            )

            auth = EasyJWTAuthentication()
            request = MagicMock()
            request.META = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
            request.headers = {"Authorization": f"Bearer {access_token}"}

            with pytest.raises(exceptions.AuthenticationFailed):
                auth.authenticate(request)


@pytest.mark.django_db
class TestModelBackend:
    def test_authenticate_returns_user(self, user):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"access": "test-access-token", "refresh": "test-refresh-token"},
                status=200,
            )
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                json={
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=200,
            )

            backend = ModelBackend()
            result = backend.authenticate(None, username="test@example.com", password="testpass123")

            assert result is not None
            assert result.email == user.email

    def test_authenticate_invalid_credentials_returns_none(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"detail": "Invalid credentials"},
                status=401,
            )

            backend = ModelBackend()
            result = backend.authenticate(None, username="wrong@example.com", password="wrongpass")

            assert result is None

    def test_get_user_returns_user(self, user):
        backend = ModelBackend()
        result = backend.get_user(user.id)

        assert result == user

    def test_get_user_not_found_returns_none(self):
        backend = ModelBackend()
        result = backend.get_user(999999)

        assert result is None
