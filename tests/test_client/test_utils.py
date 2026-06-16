import json

import pytest
import responses as responses_mock
from rest_framework import exceptions

from easyjwt_client.utils import TokenManager
from easyjwt_user.models import User


class TestTokenManager:
    def test_authenticate_returns_tokens(self, user_credentials):
        with responses_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"access": "test_access_token", "refresh": "test_refresh_token"},
                status=200,
            )

            tm = TokenManager()
            tokens = tm.authenticate(create_local_user=False, **user_credentials)

            assert "access" in tokens
            assert "refresh" in tokens

    def test_verify_returns_success(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={},
                status=200,
            )

            tm = TokenManager()
            result = tm.verify("some_token")

            assert result == {}

    def test_refresh_returns_new_access_token(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                json={"access": "new_access_token"},
                status=200,
            )

            tm = TokenManager()
            result = tm.refresh("some_refresh_token")

            assert "access" in result

    def test_connection_error_raises_authentication_failed(self, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                body=responses_mock.ConnectionError("Connection failed"),
            )

            tm = TokenManager()

            with pytest.raises(exceptions.AuthenticationFailed, match="Connection Error"):
                tm.authenticate(create_local_user=False, **user_credentials)

    def test_non_json_response_raises_authentication_failed(self, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                body="Not JSON",
                content_type="text/html",
                status=200,
            )

            tm = TokenManager()

            with pytest.raises(exceptions.AuthenticationFailed, match="incorrect content-type"):
                tm.authenticate(create_local_user=False, **user_credentials)

    def test_401_response_raises_authentication_failed(self, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"detail": "Invalid credentials"},
                status=401,
            )

            tm = TokenManager()

            with pytest.raises(exceptions.AuthenticationFailed):
                tm.authenticate(create_local_user=False, **user_credentials)

    def test_timeout_raises_authentication_failed(self, user_credentials):
        import requests

        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                body=requests.exceptions.Timeout("Request timed out"),
            )

            tm = TokenManager()

            with pytest.raises(exceptions.AuthenticationFailed, match="Timed Out"):
                tm.authenticate(create_local_user=False, **user_credentials)

    def test_malformed_json_body_raises_unhandled_error(self, user_credentials):
        """BUG-7: response.json() is not guarded against JSONDecodeError.

        A correctly-typed (application/json) but malformed body raises an
        unhandled JSONDecodeError instead of a clean AuthenticationFailed.
        """
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                body="malformed{json",
                content_type="application/json",
                status=200,
            )

            tm = TokenManager()

            with pytest.raises(json.JSONDecodeError):
                tm.authenticate(create_local_user=False, **user_credentials)


@pytest.mark.django_db
class TestCreateOrUpdateUser:
    """Tests for TokenManager._create_or_update_user — the production-default
    code path when authenticate(create_local_user=True).

    Also exercises SEC-2 (raw response.text leaked) and TEST-2.
    """

    def _mock_user_endpoint(self, rsps, user_data, access_token="fake_access"):
        rsps.add(
            responses_mock.GET,
            "http://remote-auth.test/auth/user/",
            json=user_data,
            status=200,
        )
        return {"access": access_token, "refresh": "fake_refresh"}

    def test_creates_new_local_user(self):
        user_data = {
            "id": 999,
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }

        with responses_mock.RequestsMock() as rsps:
            tokens = self._mock_user_endpoint(rsps, user_data)

            tm = TokenManager()
            user, is_new = tm._create_or_update_user(tokens)

            assert is_new is True
            assert user.email == "newuser@example.com"
            assert user.first_name == "New"

    def test_updates_existing_local_user(self, user):
        user_data = {
            "id": user.id,
            "email": user.email,
            "first_name": "Updated",
            "last_name": "Name",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }

        with responses_mock.RequestsMock() as rsps:
            tokens = self._mock_user_endpoint(rsps, user_data)

            tm = TokenManager()
            updated_user, is_new = tm._create_or_update_user(tokens)

            assert is_new is False
            assert updated_user.pk == user.pk
            assert updated_user.first_name == "Updated"

    def test_non_200_response_leaks_upstream_text(self):
        """SEC-2: non-200 response raises AuthenticationFailed with raw
        response.text, leaking auth-service internals to the client."""
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                body="Internal Server Error: traceback details...",
                status=500,
            )

            tm = TokenManager()

            with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
                tm._create_or_update_user({"access": "fake_token"})

            assert "Internal Server Error" in str(exc_info.value.detail)

    def test_authenticate_with_create_local_user_true(self, user_credentials):
        """TEST-2: authenticate() with the production default
        create_local_user=True exercises _create_or_update_user."""
        user_data = {
            "id": 1,
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }

        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"access": "test_access", "refresh": "test_refresh"},
                status=200,
            )
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                json=user_data,
                status=200,
            )

            tm = TokenManager()
            tokens = tm.authenticate(**user_credentials)

            assert "access" in tokens
            assert User.objects.filter(email="test@example.com").exists()


@pytest.mark.django_db
class TestPasswordChange:
    def test_password_change_calls_remote(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/password-change/",
                json={"detail": "Password changed."},
                status=200,
            )

            tm = TokenManager()
            result = tm.password_change("user@example.com", "old_pass", "new_pass")

            assert "detail" in result
