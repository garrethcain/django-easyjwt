from datetime import timedelta

SECRET_KEY = "test-secret-key-for-testing-only-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "easyjwt_auth",
    "easyjwt_auth.token_blacklist",
    "easyjwt_user",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "easyjwt_auth.urls"

AUTH_USER_MODEL = "easyjwt_user.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("easyjwt_auth.authentication.JWTAuthentication",),
}

EASY_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "easyjwt_auth.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("easyjwt_auth.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "easyjwt_auth.models.TokenUser",
    "JTI_CLAIM": "jti",
    "CHECK_REVOKE_TOKEN": False,
    "REVOKE_TOKEN_CLAIM": "hash_password",
    "REMOTE_AUTH_SERVICE_URL": "http://remote-auth.test",
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/",
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/",
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/",
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/user/",
    "USER_MODEL_SERIALIZER": "easyjwt_user.serializers.TokenUserSerializer",
}

USE_TZ = True
