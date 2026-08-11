from urllib.parse import urlsplit

from django.conf import settings as django_settings
from django.core.checks import Error, Warning, register

from .settings import api_settings

REQUIRED_STRING_SETTINGS = (
    "REMOTE_AUTH_SERVICE_URL",
    "REMOTE_AUTH_SERVICE_TOKEN_PATH",
    "REMOTE_AUTH_SERVICE_REFRESH_PATH",
    "REMOTE_AUTH_SERVICE_VERIFY_PATH",
    "REMOTE_AUTH_SERVICE_USER_PATH",
    "REMOTE_AUTH_SERVICE_PASSWORD_CHANGE_PATH",
    "REMOTE_AUTH_SERVICE_BLACKLIST_PATH",
)


def get_missing_required_settings():
    """Return the list of required EASY_JWT settings that are not populated.

    A value sourced from an unset environment variable (e.g.
    ``os.environ.get(...)``) resolves to ``None``; such values are reported
    rather than silently coerced, since defaulting a value like
    ``REMOTE_AUTH_SERVICE_URL`` could route auth traffic to the wrong host.
    """
    missing = []

    for key in REQUIRED_STRING_SETTINGS:
        value = getattr(api_settings, key, None)
        if not isinstance(value, str) or not value:
            missing.append(key)

    timeout = getattr(api_settings, "REMOTE_AUTH_REQUEST_TIMEOUT", None)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        missing.append("REMOTE_AUTH_REQUEST_TIMEOUT")

    ssl_verify = getattr(api_settings, "REMOTE_AUTH_SSL_VERIFY", None)
    if not isinstance(ssl_verify, bool):
        missing.append("REMOTE_AUTH_SSL_VERIFY")

    return missing


@register()
def check_required_settings(app_configs, **kwargs):
    """System check: fail ``manage.py check`` when required settings are unset."""
    return [
        Error(
            f"EASY_JWT setting '{key}' is required but not configured.",
            hint=(
                "Set it in the EASY_JWT settings dict, or provide the "
                "environment variable it is sourced from."
            ),
            id="easyjwt_client.E001",
        )
        for key in get_missing_required_settings()
    ]


def _normalize_origin(value):
    """Return a normalized ``"scheme://host[:port]"`` string, or None if invalid.

    A valid origin has no path, query, or fragment and no trailing slash.
    Used to validate ``ALLOWED_AUTH_ORIGINS`` entries.
    """
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        return None
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        return None
    return f"{parts.scheme}://{parts.netloc}".rstrip("/")


@register()
def check_cookie_mode_config(app_configs, **kwargs):
    """System checks for refresh-token cookie mode.

    Only active when ``REFRESH_TOKEN_IN_COOKIE`` is True, so installations
    that have not opted into cookie mode see no warnings or errors from
    these checks.
    """
    errors = []

    if not getattr(api_settings, "REFRESH_TOKEN_IN_COOKIE", False):
        return errors

    # E002: Django's CsrfViewMiddleware is required both for csrf_protect on
    # the obtain/refresh/logout views and for ensure_csrf_cookie on /csrf/ to
    # actually emit the Set-Cookie header in the response.
    csrf_middleware = "django.middleware.csrf.CsrfViewMiddleware"
    if csrf_middleware not in django_settings.MIDDLEWARE:
        errors.append(
            Error(
                "REFRESH_TOKEN_IN_COOKIE is enabled but "
                "django.middleware.csrf.CsrfViewMiddleware is not in MIDDLEWARE.",
                hint=(
                    "Cookie mode applies csrf_protect to the obtain/refresh/logout "
                    "views and ships a /csrf/ bootstrap endpoint; both require "
                    "CsrfViewMiddleware to be active."
                ),
                id="easyjwt_client.E002",
            )
        )

    # E003: ALLOWED_AUTH_ORIGINS, when set, must be a collection of bare
    # "http(s)://host[:port]" strings with no path/query/fragment.
    allowed_origins = getattr(api_settings, "ALLOWED_AUTH_ORIGINS", None)
    if allowed_origins is not None:
        if isinstance(allowed_origins, str) or not hasattr(allowed_origins, "__iter__"):
            errors.append(
                Error(
                    "ALLOWED_AUTH_ORIGINS must be a list/tuple of origin strings, not a single string.",
                    id="easyjwt_client.E003",
                )
            )
        else:
            for entry in allowed_origins:
                if _normalize_origin(entry) is None:
                    errors.append(
                        Error(
                            f"ALLOWED_AUTH_ORIGINS entry {entry!r} is malformed. "
                            "Each entry must be a bare 'http(s)://host[:port]' "
                            "with no path, query, fragment, or trailing slash.",
                            id="easyjwt_client.E003",
                        )
                    )

    # W001: AUTH_COOKIE_SECURE should be True in production over HTTPS.
    # Gated on REFRESH_TOKEN_IN_COOKIE so non-cookie installs don't see noise.
    if not getattr(api_settings, "AUTH_COOKIE_SECURE", False) and not django_settings.DEBUG:
        errors.append(
            Warning(
                "AUTH_COOKIE_SECURE is False while DEBUG=False and cookie mode "
                "is enabled; the refresh cookie will be transmitted over plain HTTP.",
                hint="Set AUTH_COOKIE_SECURE=True in production behind HTTPS.",
                id="easyjwt_client.W001",
            )
        )

    # W002: CSRF_COOKIE_HTTPONLY=True prevents JavaScript from reading the
    # csrftoken cookie, which breaks the library's default /csrf/ bootstrap
    # pattern. The configuration is valid if the consumer provides an
    # alternative token-delivery mechanism (e.g. rendered {% csrf_token %}).
    if getattr(django_settings, "CSRF_COOKIE_HTTPONLY", False):
        errors.append(
            Warning(
                "CSRF_COOKIE_HTTPONLY=True is incompatible with the library's "
                "default /csrf/ bootstrap endpoint: JavaScript cannot read the "
                "csrftoken cookie.",
                hint=(
                    "Provide an alternative CSRF token source such as a rendered "
                    "{% csrf_token %} in HTML or a custom endpoint that returns "
                    "the token in its JSON body."
                ),
                id="easyjwt_client.W002",
            )
        )

    return errors
