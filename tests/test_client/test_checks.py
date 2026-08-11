import logging

import pytest
from django.apps import apps
from django.test import override_settings

from easyjwt_client import checks
from easyjwt_client.settings import api_settings


def _ready():
    apps.get_app_config("easyjwt_client").ready()


class TestGetMissingRequiredSettings:
    def test_all_populated_returns_empty(self):
        assert checks.get_missing_required_settings() == []

    def test_missing_url_is_reported(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SERVICE_URL", None, raising=False)
        assert "REMOTE_AUTH_SERVICE_URL" in checks.get_missing_required_settings()

    def test_empty_string_url_is_reported(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SERVICE_URL", "", raising=False)
        assert "REMOTE_AUTH_SERVICE_URL" in checks.get_missing_required_settings()

    @pytest.mark.parametrize(
        "key",
        [
            "REMOTE_AUTH_SERVICE_TOKEN_PATH",
            "REMOTE_AUTH_SERVICE_REFRESH_PATH",
            "REMOTE_AUTH_SERVICE_VERIFY_PATH",
            "REMOTE_AUTH_SERVICE_USER_PATH",
            "REMOTE_AUTH_SERVICE_PASSWORD_CHANGE_PATH",
        ],
    )
    def test_each_path_flagged_when_none(self, key, monkeypatch):
        monkeypatch.setattr(api_settings, key, None, raising=False)
        assert key in checks.get_missing_required_settings()

    @pytest.mark.parametrize("value", [None, 0, -1, "30"])
    def test_timeout_invalid_is_flagged(self, value, monkeypatch):
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_REQUEST_TIMEOUT", value, raising=False)
        assert "REMOTE_AUTH_REQUEST_TIMEOUT" in checks.get_missing_required_settings()

    def test_ssl_verify_none_is_flagged(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SSL_VERIFY", None, raising=False)
        assert "REMOTE_AUTH_SSL_VERIFY" in checks.get_missing_required_settings()


class TestReadyGuard:
    def test_ready_does_not_crash_when_url_none(self, caplog, monkeypatch):
        caplog.set_level(logging.ERROR, logger="easyjwt_client")
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SERVICE_URL", None, raising=False)

        _ready()

        assert any(
            "not configured" in record.getMessage() and "REMOTE_AUTH_SERVICE_URL" in record.getMessage()
            for record in caplog.records
        )
        assert not any("uses http://" in r.getMessage() for r in caplog.records)

    def test_ready_runs_http_warning_when_configured(self, caplog):
        caplog.set_level(logging.WARNING, logger="easyjwt_client")
        with override_settings(DEBUG=False):
            _ready()
        assert any("uses http://" in r.getMessage() for r in caplog.records)

    def test_ready_warns_when_ssl_verify_disabled(self, caplog, monkeypatch):
        caplog.set_level(logging.WARNING, logger="easyjwt_client")
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SSL_VERIFY", False, raising=False)
        with override_settings(DEBUG=False):
            _ready()
        assert any("REMOTE_AUTH_SSL_VERIFY is disabled" in r.getMessage() for r in caplog.records)


class TestRegisteredCheck:
    def test_returns_error_for_missing_url(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REMOTE_AUTH_SERVICE_URL", None, raising=False)
        errors = checks.check_required_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "easyjwt_client.E001"
        assert "REMOTE_AUTH_SERVICE_URL" in errors[0].msg

    def test_returns_empty_when_configured(self):
        assert checks.check_required_settings(None) == []


class TestCookieModeChecks:
    """Tests for E002/E003/W001/W002 — the cookie-mode system checks."""

    def test_checks_silent_when_cookie_mode_disabled(self):
        """No cookie-mode warnings/errors when REFRESH_TOKEN_IN_COOKIE is False."""
        errors = checks.check_cookie_mode_config(None)
        assert errors == []

    def test_e002_csrf_middleware_missing(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        middleware_without_csrf = [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
        ]
        with override_settings(MIDDLEWARE=middleware_without_csrf):
            errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.E002" in ids

    def test_e002_not_raised_when_middleware_present(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.E002" not in ids

    def test_e003_malformed_origin_with_path(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        monkeypatch.setattr(api_settings, "ALLOWED_AUTH_ORIGINS", ["https://app.com/login"])
        errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.E003" in ids

    def test_e003_not_raised_for_valid_origin(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        monkeypatch.setattr(api_settings, "ALLOWED_AUTH_ORIGINS", ["https://app.com"])
        errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.E003" not in ids

    def test_w001_insecure_cookie_outside_debug(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        monkeypatch.setattr(api_settings, "AUTH_COOKIE_SECURE", False)
        with override_settings(DEBUG=False):
            errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.W001" in ids

    def test_w001_not_raised_when_cookie_mode_off(self, monkeypatch):
        """W001 must be gated on cookie mode to avoid noise on body-only installs."""
        monkeypatch.setattr(api_settings, "AUTH_COOKIE_SECURE", False)
        with override_settings(DEBUG=False):
            errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.W001" not in ids

    def test_w002_csrf_httponly_incompatible(self, monkeypatch):
        monkeypatch.setattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", True)
        with override_settings(CSRF_COOKIE_HTTPONLY=True):
            errors = checks.check_cookie_mode_config(None)
        ids = [e.id for e in errors]
        assert "easyjwt_client.W002" in ids
