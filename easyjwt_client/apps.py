import logging

from django.apps import AppConfig

from .settings import api_settings

logger = logging.getLogger("easyjwt_client")


class EasyJWTClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "easyjwt_client"

    def ready(self):
        from django.conf import settings

        from . import checks  # noqa: F401  (registers the system check)

        missing = checks.get_missing_required_settings()
        if missing:
            logger.error(
                "Required EASY_JWT settings are not configured: %s. "
                "Remote auth calls will fail until they are set.",
                ", ".join(missing),
            )
            return

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
