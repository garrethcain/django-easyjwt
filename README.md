# Django-EasyJWT

[![PyPI version](https://badge.fury.io/py/django-easyjwt.svg)](https://pypi.org/project/django-easyjwt/)
[![Python](https://img.shields.io/pypi/pyversions/django-easyjwt.svg)](https://pypi.org/project/django-easyjwt/)
[![Django](https://img.shields.io/badge/Django-3.2%20%7C%204.x%20%7C%205.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Django package for implementing remote JWT authentication in microservice architectures. It provides a centralized authentication service with multiple client services authenticating against it.

## Table of Contents

- [Why Django-EasyJWT?](#why-django-easyjwt)
- [Features](#features)
- [Installation](#installation)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
  - [Create an Auth-Service](#create-an-auth-service)
  - [Create a Client-Service](#create-a-client-service)
  - [Standing up the Services](#standing-up-the-services)
- [Configuration Reference](#configuration-reference)
- [API Endpoints](#api-endpoints)
- [Testing the API](#testing-the-api)
- [Advanced Usage](#advanced-usage)
  - [Extra Data](#extra-data)
  - [Permissions](#permissions)
- [Running Tests](#running-tests)
- [Changelog](#changelog)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## Why Django-EasyJWT?

When managing multiple services with the same users, a centralized authentication service eliminates password confusion and provides a single source of truth. Django-EasyJWT was built for scenarios where:

- Multiple services share the same user base
- Different services require different access levels
- You need custom user data and permissions passed through authentication
- You want to keep your auth service lean and behind a private network

---

## Features

- **JWT Authentication**: Access and refresh token support
- **Remote Auth**: Client services authenticate against a central auth service
- **Session Support**: Authenticated users can access Django admin
- **Custom User Model**: Optional email-based user model included
- **Token Blacklisting**: Optional token revocation support
- **Extensible**: Custom serializers for additional user data
- **Configurable Timeouts**: HTTP request timeouts and SSL verification

---

## Installation

```bash
uv pip install django-easyjwt
```

Or with pip:

```bash
pip install django-easyjwt
```

---

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐
│  Client-Service │ ──────► │   Auth-Service  │
│   (Port 8001)   │         │   (Port 8000)   │
├─────────────────┤         ├─────────────────┤
│ easyjwt_client  │         │  easyjwt_auth   │
│ easyjwt_user    │         │  easyjwt_user   │
└─────────────────┘         └─────────────────┘
        │                           │
        ▼                           ▼
   Local DB                     Auth DB
 (User copies)              (User source)
```

The package contains three sub-packages:

| Package          | Used In         | Purpose                                    |
| ---------------- | --------------- | ------------------------------------------ |
| `easyjwt_auth`   | Auth-Service    | JWT token generation and validation        |
| `easyjwt_client` | Client-Service  | Remote authentication against auth-service |
| `easyjwt_user`   | Both (optional) | Custom user model with email as username   |

---

## Quick Start

### Create an Auth-Service

```bash
uv venv
source .venv/bin/activate
uv pip install django djangorestframework django_easyjwt
uv run django-admin startproject config
mv config auth-service
cd auth-service
```

Add to `config/settings.py`:

```python
from datetime import timedelta

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'easyjwt_auth',
    'easyjwt_user',
]

AUTH_USER_MODEL = "easyjwt_user.User"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "easyjwt_auth.authentication.JWTAuthentication",
    ),
}

EASY_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": "d577273ff885c3f84dadb8578bb40000",  # Set properly for production!
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "easyjwt_auth.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("easyjwt_auth.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "easyjwt_auth.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}
```

Add to `config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('auth/', include('easyjwt_auth.urls')),
    path('auth/', include('easyjwt_user.urls')),
]
```

Run migrations and create a superuser:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver 0.0.0.0:8000
```

---

### Create a Client-Service

```bash
cd ..
uv venv
source .venv/bin/activate
uv pip install django django_rest_framework django_easyjwt
uv run django-admin startproject config
mv config client-service
cd client-service
```

Add to `config/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'easyjwt_client',
    'easyjwt_user',
]

AUTH_USER_MODEL = "easyjwt_user.User"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "easyjwt_client.authentication.EasyJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'easyjwt_client.authentication.RemoteAuthBackend',
]

EASY_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "Authorization",
    "REMOTE_AUTH_SERVICE_URL": "http://127.0.0.1:8000",
    "REMOTE_AUTH_SERVICE_TOKEN_PATH": "/auth/token/",
    "REMOTE_AUTH_SERVICE_REFRESH_PATH": "/auth/token/refresh/",
    "REMOTE_AUTH_SERVICE_VERIFY_PATH": "/auth/token/verify/",
    "REMOTE_AUTH_SERVICE_USER_PATH": "/auth/user/",
    "REMOTE_AUTH_REQUEST_TIMEOUT": 30,
    "REMOTE_AUTH_SSL_VERIFY": True,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

Add to `config/urls.py`:

```python
from django.urls import path, include
from test_app.views import TestView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include("easyjwt_client.urls")),
    path('api/test/', TestView.as_view()),
]
```

Create `test_app/views.py`:

```python
from rest_framework import generics
from rest_framework.response import Response

class TestView(generics.GenericAPIView):
    def get(self, request):
        return Response("success", status=200)
```

Run migrations:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8001
```

---

### Standing up the Services

Run both services in separate terminals:

```bash
# Terminal 1 - Auth-Service
cd auth-service
source .venv/bin/activate
uv run python manage.py runserver 0.0.0.0:8000

# Terminal 2 - Client-Service
cd client-service
source .venv/bin/activate
uv run python manage.py runserver 0.0.0.0:8001
```

---

## Configuration Reference

### Auth-Service Settings

| Setting                  | Type      | Default     | Description                             |
| ------------------------ | --------- | ----------- | --------------------------------------- |
| `ACCESS_TOKEN_LIFETIME`  | timedelta | Required    | Access token validity duration          |
| `REFRESH_TOKEN_LIFETIME` | timedelta | Required    | Refresh token validity duration         |
| `ALGORITHM`              | str       | `"HS256"`   | JWT signing algorithm                   |
| `SIGNING_KEY`            | str       | Required    | Secret key for signing tokens           |
| `USER_ID_FIELD`          | str       | `"id"`      | User model field for ID                 |
| `USER_ID_CLAIM`          | str       | `"user_id"` | JWT claim for user ID                   |
| `CHECK_REVOKE_TOKEN`     | bool      | `False`     | Enable password-change token revocation |

### Client-Service Settings

| Setting                            | Type  | Default                  | Description                     |
| ---------------------------------- | ----- | ------------------------ | ------------------------------- |
| `REMOTE_AUTH_SERVICE_URL`          | str   | Required                 | Base URL of auth-service        |
| `REMOTE_AUTH_SERVICE_TOKEN_PATH`   | str   | `"/auth/token/"`         | Token endpoint path             |
| `REMOTE_AUTH_SERVICE_REFRESH_PATH` | str   | `"/auth/token/refresh/"` | Refresh endpoint path           |
| `REMOTE_AUTH_SERVICE_VERIFY_PATH`  | str   | `"/auth/token/verify/"`  | Verify endpoint path            |
| `REMOTE_AUTH_SERVICE_USER_PATH`    | str   | `"/auth/user/"`          | User endpoint path              |
| `REMOTE_AUTH_REQUEST_TIMEOUT`      | int   | `30`                     | HTTP request timeout in seconds |
| `REMOTE_AUTH_SSL_VERIFY`           | bool  | `True`                   | Verify SSL certificates         |
| `AUTH_HEADER_TYPES`                | tuple | `("Bearer",)`            | Valid auth header types         |
| `USER_MODEL_SERIALIZER`            | str   | Built-in                 | Custom user serializer path     |

---

## API Endpoints

| Endpoint               | Method | Description                      |
| ---------------------- | ------ | -------------------------------- |
| `/auth/token/`         | POST   | Obtain access and refresh tokens |
| `/auth/token/refresh/` | POST   | Refresh an expired access token  |
| `/auth/token/verify/`  | POST   | Verify if a token is valid       |
| `/auth/users/`         | GET    | List users (auth-service only)   |
| `/auth/users/{id}/`    | GET    | Get user details                 |

---

## Testing the API

### Obtain Token Pair

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "user-pass"}' \
  http://127.0.0.1:8001/auth/token/
```

Response:

```json
{
  "refresh": "...",
  "access": "..."
}
```

### Make Authenticated Request

```bash
export ACCESS_TOKEN=<your_access_token>

curl -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  http://127.0.0.1:8001/api/test/
```

Response: `"success"`

### Refresh Token

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"refresh": "${REFRESH_TOKEN}"}' \
  http://127.0.0.1:8001/auth/token/refresh/
```

### Verify Token

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"token": "${ACCESS_TOKEN}"}' \
  http://127.0.0.1:8001/auth/token/verify/
```

---

## Advanced Usage

### Extra Data

You can pass additional user data from the auth-service to client-services using custom serializers.

#### Auth-Service Configuration

`models.py`:

```python
class AccessGroup(models.Model):
    user = models.OneToOneField(User, related_name="accessgroup", on_delete=models.CASCADE)
    user_type = models.TextField()
```

`serializers.py`:

```python
class AccessGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessGroup
        fields = ("user_type",)

class TokenUserSerializer(serializers.ModelSerializer):
    accessgroup = AccessGroupSerializer()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "accessgroup")
```

Add to `EASY_JWT` settings:

```python
"USER_MODEL_SERIALIZER": "userdata.serializers.TokenUserSerializer",
```

#### Client-Service Configuration

Use the same model and serializer, but override `create()` and `update()` methods:

```python
class TokenUserSerializer(serializers.ModelSerializer):
    accessgroup = AccessGroupSerializer()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "accessgroup")

    def create(self, validated_data):
        accessgroup = validated_data.pop("accessgroup")
        user, _ = User.objects.get_or_create(
            email=validated_data.pop("email"),
            defaults=validated_data
        )
        AccessGroup.objects.update_or_create(user=user, defaults=accessgroup)
        return user

    def update(self, instance, validated_data):
        accessgroup = validated_data.pop("accessgroup")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        AccessGroup.objects.update_or_create(user=instance, defaults=accessgroup)
        return instance
```

---

### Permissions

Use custom permission classes to control access based on user data:

```python
from rest_framework import permissions

class AccessGroupPermission(permissions.BasePermission):
    message = "You do not have permission to this service"

    def has_permission(self, request, view):
        return (
            not request.user.is_anonymous
            and hasattr(request.user, 'accessgroup')
            and view.access_level.startswith(request.user.accessgroup.user_type)
        )
```

---

## Running Tests

```bash
uv pip install -e ".[dev]"
uv run pytest
```

Or with coverage:

```bash
uv run pytest --cov=easyjwt_auth --cov=easyjwt_client --cov=easyjwt_user
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

### Recent Changes (1.0.0)

- Replaced MD5 with SHA-256 for password hashing
- Renamed `ModelBackend` to `RemoteAuthBackend`
- Added configurable HTTP request timeouts
- Made SSL verification configurable
- Consolidated HTTP error handling
- Added `__all__` exports to public modules

---

## Acknowledgements

This package is heavily based on [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) and influenced by SimpleJWT.

An example implementation is available at [django-easyjwt-example](https://github.com/garrethcain/django-easyjwt-example).

---

## License

MIT License - see [LICENCE](LICENCE) file.
