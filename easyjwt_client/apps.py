import logging

from django.apps import AppConfig

from .settings import api_settings

logger = logging.getLogger("easyjwt_client")


class EasyJWTClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "easyjwt_client"

    def ready(self):
        from django.conf import settings

        if not settings.DEBUG:
            if not api_settings.REMOTE_AUTH_SSL_VERIFY:
                logger.warning(
                    "REMOTE_AUTH_SSL_VERIFY is disabled — HTTP requests to "
                    "the auth service will not verify SSL certificates."
                )
            if api_settings.REMOTE_AUTH_SERVICE_URL.startswith("http://"):
                logger.warning(
                    "REMOTE_AUTH_SERVICE_URL uses http:// — credentials and "
                    "tokens will be transmitted in cleartext to %s",
                    api_settings.REMOTE_AUTH_SERVICE_URL,
                )
