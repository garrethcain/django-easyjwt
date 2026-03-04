import pytest
import responses as responses_mock
from rest_framework import exceptions

from easyjwt_client.utils import TokenManager


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
