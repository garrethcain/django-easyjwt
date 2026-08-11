from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings as _APISettings


USER_SETTINGS = getattr(settings, "EASY_JWT", None)

DEFAULTS = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "Authorization",  # I think this config is broken in this ver of the Simple-JWT lib.
    "REMOTE_AUTH_SERVICE_URL": "http://127.0.0.1:8000",  # Were do we reach the Auth-Service
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/",  # The path to login and retrieve a token
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/",  # The path to refresh a token
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/",  # The path to verify a token
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/user/",  # the path to get the user object from the remote auth service
    "REMOTE_AUTH_SERVICE_PASSWORD_CHANGE_PATH": "/auth/password-change/",  # the path to change password on the remote auth service
    "REMOTE_AUTH_SERVICE_BLACKLIST_PATH": "/auth/token/blacklist/",  # the path to blacklist a refresh token on the remote auth service
    "REMOTE_AUTH_REQUEST_TIMEOUT": 30,  # Timeout in seconds for HTTP requests
    "REMOTE_AUTH_SSL_VERIFY": True,  # Enable SSL certificate verification
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_MODEL_SERIALIZER": "easyjwt_user.serializers.TokenUserSerializer",
    # --- Refresh-token cookie support (opt-in) ---
    # When REFRESH_TOKEN_IN_COOKIE is False (the default), the client app behaves
    # exactly as before: refresh tokens are returned in the JSON body and no
    # cookies are set. Enable cookie mode for browser-based clients so the
    # refresh token is stored in an HttpOnly cookie and never exposed to
    # JavaScript. Non-browser clients (mobile, server-to-server) should leave
    # this False and continue reading refresh tokens from the JSON body.
    "REFRESH_TOKEN_IN_COOKIE": False,
    "AUTH_COOKIE_NAME": "refresh_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SECURE": False,  # W001 warns when DEBUG=False; set True in production over HTTPS
    "AUTH_COOKIE_SAMESITE": "Lax",
    # Cookie identity is name + domain + path; the browser only sends the
    # cookie to URLs under this path. The default "/" works regardless of
    # where easyjwt_client.urls is mounted. Narrow this to the public URL
    # prefix (e.g. "/auth/token/") for tighter scoping once you know your
    # mount point.
    "AUTH_COOKIE_PATH": "/",
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_MAX_AGE": None,  # None = session cookie; cap at refresh-token lifetime for persistence
    # Optional defense-in-depth: exact-origin allowlist for cookie-bearing
    # endpoints (obtain/refresh/logout). Each entry must be a bare
    # "http(s)://host[:port]" with no path/query/fragment and no trailing slash.
    # None disables the explicit check (Django's CSRF Origin validation remains).
    "ALLOWED_AUTH_ORIGINS": None,
    "BLACKLIST_ON_LOGOUT": True,  # Best-effort server-side refresh-token revocation on logout
}

IMPORT_STRINGS = (
    "AUTH_TOKEN_CLASSES",
    "TOKEN_USER_CLASS",
    "USER_AUTHENTICATION_RULE",
)

REMOVED_SETTINGS = ("EMPTY",)


class APISettings(_APISettings):  # pragma: no cover
    def __check_user_settings(self, user_settings):
        SETTINGS_DOC = "https://django-easyjwt.readthedocs.io/en/latest/settings.html"

        for setting in REMOVED_SETTINGS:
            if setting in user_settings:
                raise RuntimeError(
                    f"The '{setting}' setting has been removed. "
                    f"Please refer to '{SETTINGS_DOC}' for available settings."
                )

        return user_settings


api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*args, **kwargs):  # pragma: no cover
    global api_settings

    setting, value = kwargs["setting"], kwargs["value"]
    if setting == "EASY_JWT":
        api_settings = APISettings(value, DEFAULTS, IMPORT_STRINGS)


setting_changed.connect(reload_api_settings)
