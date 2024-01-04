from django.conf import settings
from django.test.signals import setting_changed
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import APISettings as _APISettings


USER_SETTINGS = getattr(settings, "REMOTE_JWT", None)

DEFAULTS = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "Authorization",  # I think this config is broken in this ver of the Simple-JWT lib.
    "REMOTE_AUTH_SERVICE_URL": "http://127.0.0.1:8000",  # Were do we reach the Auth-Service
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/",  # The path to login and retrieve a token
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/",  # The path to refresh a token
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/",  # The path to verify a token
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/users/{user_id}/",  # the path to get the user object from the remote auth service
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_MODEL_SERIALIZER": "remotejwt_user.serializers.TokenUserSerializer",
}

IMPORT_STRINGS = (
    "AUTH_TOKEN_CLASSES",
    "TOKEN_USER_CLASS",
    "USER_AUTHENTICATION_RULE",
)

REMOVED_SETTINGS = ()


class APISettings(_APISettings):  # pragma: no cover
    def __check_user_settings(self, user_settings):
        SETTINGS_DOC = "https://django-rest-framework-remotejwt.readthedocs.io/en/latest/settings.html"

        for setting in REMOVED_SETTINGS:
            if setting in user_settings:
                raise RuntimeError(
                    (
                        "The '{}' setting has been removed. Please refer to '{}' for available settings."
                    ),
                    setting,
                    SETTINGS_DOC,
                )

        return user_settings


api_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*args, **kwargs):  # pragma: no cover
    global api_settings

    setting, value = kwargs["setting"], kwargs["value"]
    if setting == "REMOTE_JWT":
        api_settings = APISettings(value, DEFAULTS, IMPORT_STRINGS)


setting_changed.connect(reload_api_settings)
