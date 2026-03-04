import json

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.module_loading import import_string
from rest_framework import exceptions

from .settings import api_settings

User = get_user_model()


class TokenManager:
    """
    A tidy class to abstract some of the token
    auth, verification, and refreshing from the views.
    """

    username_field = get_user_model().USERNAME_FIELD

    def __request(self, path, payload, extra_headers=None) -> dict:
        root_url = settings.EASY_JWT["REMOTE_AUTH_SERVICE_URL"]
        headers = {
            "content-type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        try:
            response = requests.post(
                f"{root_url}{path}",
                data=json.dumps(payload),
                headers=headers,
                verify=True,
            )
        except requests.exceptions.ConnectionError as e:
            raise exceptions.AuthenticationFailed("Authentication Service Connection Error.") from e
        except requests.exceptions.Timeout as e:
            raise exceptions.AuthenticationFailed("Authentication Service Timed Out.") from e

        content_type = response.headers.get("Content-Type")
        if content_type != "application/json":
            raise exceptions.AuthenticationFailed(
                "Authentication Service response has incorrect content-type. "
                f"Expected application/json but received {content_type}"
            )

        if response.status_code not in [200, 201]:
            raise exceptions.AuthenticationFailed(
                response.json(),
                code=response.status_code,
            )
        return response.json()

    def get_csrf_token(self, path):
        # first get the csrf token so we can satisfy the requirements.
        root_url = settings.EASY_JWT["REMOTE_AUTH_SERVICE_URL"]
        session = requests.Session()
        _ = session.get(f"{root_url}/{path}")
        csrftoken = session.cookies.get("csrftoken")
        headers = {"X-CSRFToken": csrftoken}
        return headers

    def password_change(self, email, password, new_password):
        payload = dict(
            email=email,
            password=password,
            new_password=new_password,
        )
        return self.__request("/auth/password-change/", payload)

    def verify(self, token) -> dict:
        """
        Verifies a token against the remote Auth-Service.
        """
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_VERIFY_PATH"]
        payload = {"token": token}
        return self.__request(path, payload)

    def refresh(self, refresh) -> dict:
        """
        Returns an Access token by refreshing with the Refresh token
        against the remote Auth-Service.
        """
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_REFRESH_PATH"]
        payload = {"refresh": refresh}

        return self.__request(path, payload)

    def authenticate(self, create_local_user=True, *args, **kwargs):
        """
        Returns an Access & Refresh token if authenticated against the remote
        Authentication-Service.
        """
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_TOKEN_PATH"]
        payload = {
            self.username_field: kwargs[self.username_field],
            "password": kwargs.get("password"),
        }
        tokens = self.__request(path, payload)

        if create_local_user:
            _ = self._create_or_update_user(tokens)
        return tokens

    def _create_or_update_user(self, tokens):
        auth_header = settings.EASY_JWT["AUTH_HEADER_NAME"]
        auth_header_types = settings.EASY_JWT["AUTH_HEADER_TYPES"]
        root_url = settings.EASY_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_USER_PATH"]
        headers: dict[str, str] = {
            auth_header: f"{auth_header_types[0]} {tokens.get('access') if isinstance(tokens, dict) else tokens}",
            "content-type": "application/json",
        }

        request = requests.Request("GET", f"{root_url}{path}", data={}, headers=headers)
        prepped = request.prepare()
        prepped.headers.update(headers)

        with requests.Session() as session:
            try:
                response = session.send(prepped)
            except requests.exceptions.ConnectionError as e:
                raise exceptions.AuthenticationFailed("Authentication Service Connection Error.") from e
            except requests.exceptions.Timeout as e:
                raise exceptions.AuthenticationFailed("Authentication Service Timed Out.") from e
        if response.status_code != 200:
            raise exceptions.AuthenticationFailed(response.text)

        user_dict = response.json()
        try:
            existing_user = User.objects.get(**{self.username_field: user_dict[self.username_field]})
        except User.DoesNotExist:
            existing_user = None

        is_new_user = existing_user is None

        try:
            serializer = import_string(api_settings.USER_MODEL_SERIALIZER)
            s = serializer(
                existing_user,
                data=user_dict,
                context={
                    "user_id_field": settings.EASY_JWT["USER_ID_CLAIM"],
                    "raw_data": user_dict,
                },
            )
            if not s.is_valid(raise_exception=False):
                raise exceptions.AuthenticationFailed(
                    f"Integrity error with USER_MODEL_SERIALIZER: {api_settings.USER_MODEL_SERIALIZER} "
                    "failed to parse the received payload from the auth server."
                )
            user = s.save()
        except ImportError:
            msg = f"Could not import serializer '{api_settings.USER_MODEL_SERIALIZER}'"
            raise ImportError(msg)
        except IntegrityError as e:
            raise exceptions.AuthenticationFailed(
                f"Integrity error with user from Authentication Service. Different User models? {e}"
            ) from e
        return (user, is_new_user)
