import logging

import pytest
import responses as responses_mock
from django.test import RequestFactory, override_settings
from rest_framework.test import APIClient

from easyjwt_client.settings import api_settings
from easyjwt_client.utils import TokenManager
from easyjwt_client.views import PasswordChangeView


@pytest.fixture
def client_urls(settings):
    settings.ROOT_URLCONF = "tests.test_client.urls"


@pytest.fixture
def cookie_mode(monkeypatch):
    """Enable refresh-token cookie mode for the duration of a test."""
    monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)


def _mock_remote(rsps, method, url, json_body, status=200):
    rsps.add(method, url, json=json_body, status=status)


def _set_cookie(client, name, value):
    client.cookies[name] = value


def _get_csrf_token(client):
    """Bootstrap the CSRF cookie via GET /csrf/ and return its value."""
    client.get("/auth/csrf/")
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenObtainPairView:
    def test_valid_credentials_returns_tokens(self, user, user_credentials):
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
                json={
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/", user_credentials)

            assert response.status_code == 200
            data = response.json()
            assert "access" in data
            assert "refresh" in data

    def test_missing_data_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenRefreshView:
    def test_valid_refresh_returns_new_access(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                json={"access": "new_access_token"},
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/refresh/", {"refresh": "old_refresh_token"})

            assert response.status_code == 200
            assert "access" in response.json()

    def test_missing_refresh_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/refresh/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenVerifyView:
    def test_valid_token_returns_200(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={},
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/verify/", {"token": "some_token"})

            assert response.status_code == 200

    def test_missing_token_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/verify/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestPasswordChangeView:
    def test_matching_passwords_succeed(self, user):
        factory = RequestFactory()
        request = factory.post(
            "/auth/password-change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        request.user = user

        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/password-change/",
                json={"detail": "Password changed successfully."},
                status=200,
            )

            view = PasswordChangeView()
            view.request = request
            view.kwargs = {}
            response = view.post(request)

            assert response.status_code == 302

    def test_mismatched_passwords_are_rejected(self, user):
        """SEC-1: mismatched new passwords should NOT trigger a remote password change."""
        factory = RequestFactory()
        request = factory.post(
            "/auth/password-change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpass123",
                "new_password2": "different456",
            },
        )
        request.user = user

        with responses_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/password-change/",
                json={},
                status=200,
            )

            view = PasswordChangeView()
            view.request = request
            view.kwargs = {}
            response = view.post(request)

            assert response.status_code != 302


# ---------------------------------------------------------------------------
# Refresh-token cookie mode tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestCookieModeLogin:
    """TokenObtainPairView in cookie mode: sets cookie, strips refresh from body."""

    def test_login_sets_refresh_cookie(self, cookie_mode, user, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                {"access": "a1", "refresh": "r1"},
            )
            _mock_remote(
                rsps,
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                {"id": user.id, "email": user.email},
            )

            resp = APIClient().post("/auth/token/", user_credentials)

            assert resp.status_code == 200
            assert "refresh_token" in resp.cookies
            assert resp.cookies["refresh_token"].value == "r1"
            # HttpOnly + SameSite configured
            assert "HttpOnly" in resp.cookies["refresh_token"].OutputString()
            assert "Path=/auth/token/" in resp.cookies["refresh_token"].OutputString()

    def test_login_body_has_no_refresh_in_cookie_mode(self, cookie_mode, user, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                {"access": "a1", "refresh": "r1"},
            )
            _mock_remote(
                rsps,
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                {"id": user.id, "email": user.email},
            )

            resp = APIClient().post("/auth/token/", user_credentials)

            assert resp.status_code == 200
            data = resp.json()
            assert "access" in data
            assert "refresh" not in data

    def test_login_csrf_rejected_in_cookie_mode(self, cookie_mode, user, user_credentials):
        """POST without CSRF token → 403 when cookie mode is on."""
        client = APIClient(enforce_csrf_checks=True)
        resp = client.post("/auth/token/", user_credentials)
        assert resp.status_code == 403

    def test_login_csrf_accepted_with_token(self, cookie_mode, user, user_credentials):
        """POST with a valid CSRF token passes the CSRF check."""
        client = APIClient(enforce_csrf_checks=True)
        token = _get_csrf_token(client)

        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                {"access": "a1", "refresh": "r1"},
            )
            _mock_remote(
                rsps,
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                {"id": user.id, "email": user.email},
            )

            resp = client.post("/auth/token/", user_credentials, HTTP_X_CSRFTOKEN=token)
            assert resp.status_code == 200

    def test_login_origin_rejected(self, cookie_mode, monkeypatch, user, user_credentials):
        monkeypatch.setattr(api_settings, "ALLOWED_AUTH_ORIGINS", ["https://allowed.example.com"])
        resp = APIClient().post("/auth/token/", user_credentials, HTTP_ORIGIN="https://evil.example.com")
        assert resp.status_code == 403


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestCookieModeRefresh:
    """TokenRefreshView in cookie mode: strict cookie-only, rotation rewrites cookie."""

    def test_refresh_reads_from_cookie(self, cookie_mode):
        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                {"access": "new_a"},
            )

            client = APIClient()
            _set_cookie(client, "refresh_token", "stored_refresh")
            resp = client.post("/auth/token/refresh/", {})

            assert resp.status_code == 200
            assert resp.json()["access"] == "new_a"

    def test_refresh_rotation_rewrites_cookie(self, cookie_mode):
        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                {"access": "new_a", "refresh": "rotated_refresh"},
            )

            client = APIClient()
            _set_cookie(client, "refresh_token", "old_refresh")
            resp = client.post("/auth/token/refresh/", {})

            assert resp.status_code == 200
            assert resp.cookies["refresh_token"].value == "rotated_refresh"
            assert "refresh" not in resp.json()

    def test_refresh_no_cookie_returns_401(self, cookie_mode):
        resp = APIClient().post("/auth/token/refresh/", {})
        assert resp.status_code == 401

    def test_refresh_body_mode_no_cookie_returns_400(self):
        """Body-only mode preserves the 400 validation contract."""
        resp = APIClient().post("/auth/token/refresh/", {})
        assert resp.status_code == 400

    def test_refresh_cookie_precedence_over_body(self, cookie_mode, monkeypatch):
        """When both cookie and body are supplied in cookie mode, only the cookie value is used."""
        calls = []

        def fake_refresh(self, refresh):
            calls.append(refresh)
            return {"access": "new_a"}

        monkeypatch.setattr(TokenManager, "refresh", fake_refresh)

        client = APIClient()
        _set_cookie(client, "refresh_token", "cookie_value")
        client.post("/auth/token/refresh/", {"refresh": "body_value"})

        assert calls == ["cookie_value"]

    def test_refresh_csrf_rejected_in_cookie_mode(self, cookie_mode):
        client = APIClient(enforce_csrf_checks=True)
        _set_cookie(client, "refresh_token", "r1")
        resp = client.post("/auth/token/refresh/", {})
        assert resp.status_code == 403


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestCSRFBootstrap:
    def test_csrf_endpoint_sets_cookie(self):
        resp = APIClient().get("/auth/csrf/")
        assert resp.status_code == 200
        assert "csrftoken" in resp.cookies


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenLogout:
    def test_logout_clears_cookie(self, cookie_mode):
        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/blacklist/",
                {},
            )

            client = APIClient()
            _set_cookie(client, "refresh_token", "r1")
            resp = client.post("/auth/token/logout/", {})

            assert resp.status_code == 200
            assert resp.json()["detail"] == "Logged out."
            # delete_cookie sets max-age 0 and an expiry in the past
            deleted = resp.cookies["refresh_token"]
            assert deleted["max-age"] == 0 or deleted.value == ""

    def test_logout_works_without_auth(self, cookie_mode):
        """Logout is idempotent: no cookie, no Authorization → still 200."""
        resp = APIClient().post("/auth/token/logout/", {})
        assert resp.status_code == 200

    def test_logout_failed_blacklist_still_clears_cookie(self, cookie_mode, caplog):
        caplog.set_level(logging.WARNING, logger="easyjwt_client")

        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/blacklist/",
                {"detail": "error"},
                status=500,
            )

            client = APIClient()
            _set_cookie(client, "refresh_token", "r1")
            resp = client.post("/auth/token/logout/", {})

            assert resp.status_code == 200
            assert any("blacklist failed" in r.getMessage() for r in caplog.records)

    def test_logout_blacklist_disabled(self, cookie_mode, monkeypatch):
        called = []
        monkeypatch.setattr(TokenManager, "blacklist", lambda self, r: called.append(r))

        monkeypatch.setattr(api_settings, "BLACKLIST_ON_LOGOUT", False)
        client = APIClient()
        _set_cookie(client, "refresh_token", "r1")
        resp = client.post("/auth/token/logout/", {})

        assert resp.status_code == 200
        assert called == []

    def test_logout_csrf_rejected_in_cookie_mode(self, cookie_mode):
        client = APIClient(enforce_csrf_checks=True)
        _set_cookie(client, "refresh_token", "r1")
        resp = client.post("/auth/token/logout/", {})
        assert resp.status_code == 403


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestOriginValidation:
    def test_referer_with_path_under_allowed_origin(self, cookie_mode, monkeypatch):
        """Referer includes a path but should match a bare origin in the allowlist."""
        monkeypatch.setattr(api_settings, "ALLOWED_AUTH_ORIGINS", ["https://app.example.com"])

        with responses_mock.RequestsMock() as rsps:
            _mock_remote(
                rsps,
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                {"access": "new_a"},
            )

            client = APIClient()
            _set_cookie(client, "refresh_token", "r1")
            resp = client.post(
                "/auth/token/refresh/",
                {},
                HTTP_REFERER="https://app.example.com/login",
            )
            assert resp.status_code == 200

    def test_mismatched_origin_rejected(self, cookie_mode, monkeypatch):
        monkeypatch.setattr(api_settings, "ALLOWED_AUTH_ORIGINS", ["https://app.example.com"])
        resp = APIClient().post("/auth/token/refresh/", {}, HTTP_ORIGIN="https://evil.example.com")
        assert resp.status_code == 403
