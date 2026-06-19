from django.core.checks import Error, register

from .settings import api_settings

REQUIRED_STRING_SETTINGS = (
    "REMOTE_AUTH_SERVICE_URL",
    "REMOTE_AUTH_SERVICE_TOKEN_PATH",
    "REMOTE_AUTH_SERVICE_REFRESH_PATH",
    "REMOTE_AUTH_SERVICE_VERIFY_PATH",
    "REMOTE_AUTH_SERVICE_USER_PATH",
    "REMOTE_AUTH_SERVICE_PASSWORD_CHANGE_PATH",
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
