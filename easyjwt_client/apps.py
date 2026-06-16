import logging

from django.apps import AppConfig

logger = logging.getLogger("easyjwt_client")


class EasyJWTClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "easyjwt_client"

    def ready(self):
        from django.conf import settings

        easy_jwt = getattr(settings, "EASY_JWT", {})
        ssl_verify = easy_jwt.get("REMOTE_AUTH_SSL_VERIFY", True)
        remote_url = easy_jwt.get("REMOTE_AUTH_SERVICE_URL", "")

        if not settings.DEBUG:
            if not ssl_verify:
                logger.warning(
                    "REMOTE_AUTH_SSL_VERIFY is disabled — HTTP requests to "
                    "the auth service will not verify SSL certificates."
                )
            if remote_url.startswith("http://"):
                logger.warning(
                    "REMOTE_AUTH_SERVICE_URL uses http:// — credentials and "
                    "tokens will be transmitted in cleartext to %s",
                    remote_url,
                )
