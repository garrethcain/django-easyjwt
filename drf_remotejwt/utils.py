import json
import requests
import json
import requests

from typing import Tuple
from base64 import b64decode

from rest_framework import generics, exceptions

from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth import get_user_model


User = get_user_model()


class TokenManager:
    """
    A tidy class to abstract some of the token
    auth, verification, and refreshing from the views.
    """
    username_field = get_user_model().USERNAME_FIELD

    def __request(self, path, payload) -> dict:
        root_url = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_URL"]
        headers = {
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                f"{root_url}{path}",
                data=json.dumps(payload),
                headers=headers,
                verify=True,
            )
        except requests.exceptions.ConnectionError as e:
            raise exceptions.AuthenticationFailed(
                "Authentication Service Connection Error."
            ) from e
        except requests.exceptions.Timeout as e:
            raise exceptions.AuthenticationFailed(
                "Authentication Service Timed Out."
            ) from e

        content_type = response.headers.get('Content-Type')
        if content_type != 'application/json':
            raise exceptions.AuthenticationFailed(
                "Authentication Service response has incorrect content-type. " \
                f"Expected application/json but received {content_type}"
            )

        if response.status_code != 200:
            raise exceptions.AuthenticationFailed(
                response.json(),
                code=response.status_code,
            )
        return response.json()

    def verify(self, token) -> dict:
        """
        Verifies a token against the remote Auth-Service.
        """
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_VERIFY_PATH"]
        payload = {
            "token": token
        }
        return self.__request(path, payload)

    def refresh(self, refresh) -> dict:
        """
        Returns an Access token by refreshing with the Refresh token
        against the remote Auth-Service.
        """
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_REFRESH_PATH"]
        payload = {
            "refresh": refresh
        }

        return self.__request(path, payload)

    def authenticate(self, create_local_user=True, *args, **kwargs):
        """
        Returns an Access & Refresh token if authenticated against the remote
        Authentication-Service.
        """
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_TOKEN_PATH"]
        payload = {
            self.username_field: kwargs[self.username_field],
            "password": kwargs.get("password")
        }
        tokens = self.__request(path, payload)

        if create_local_user:
            # Do we need to do something with these objects?
            user, created = self.__create_or_update_user(tokens)
        return tokens

    def __parse_auth_string(self, auth_string: str) -> Tuple[dict, dict, str]:
        header, payload, signature = auth_string.split(".")
        header_str = b64decode(header)
        payload_str = b64decode(f"{payload}==")  # add padding back on.
        # signature = b64decode(f"{signature}==")
        return (json.loads(header_str), json.loads(payload_str), signature)

    def __create_or_update_user(self, tokens):
        header_dict, payload_dict, signature = self.__parse_auth_string(tokens["access"])
        user_id = payload_dict[settings.REMOTE_JWT["USER_ID_CLAIM"]]
        auth_header = settings.REMOTE_JWT['AUTH_HEADER_NAME']
        auth_header_type = settings.REMOTE_JWT["AUTH_HEADER_TYPE"]
        root_url = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_USER_PATH"].format(
            user_id=user_id
        )
        headers: dict[str, str] = {
            auth_header: f"{auth_header_type} {tokens.get('access')}",
            "content-type": "application/json",
        }

        request = requests.Request("GET", f"{root_url}{path}", data={}, headers=headers)
        prepped = request.prepare()
        prepped.headers.update(headers)

        with requests.Session() as session:
            try:
                response = session.send(prepped)
            except requests.exceptions.ConnectionError as e:
                raise exceptions.AuthenticationFailed(
                    "Authentication Service Connection Error."
                ) from e
            except requests.exceptions.Timeout as e:
                raise exceptions.AuthenticationFailed(
                    "Authentication Service Timed Out."
                ) from e
        if response.status_code != 200:
            raise exceptions.AuthenticationFailed(response.json())
        
        user_dict = response.json()
        user_id = user_dict.pop("id")
        try:
            user, created = User.objects.update_or_create(
                id=user_id,
                defaults={**user_dict}
            )
        except IntegrityError as e:
            # This is most likely caused by having two different User models.
            # Eg. a Custom User model in Auth-Service and a vanilla User in 
            # your client project.
            raise exceptions.AuthenticationFailed("Integrity error with user from Authentication Service. Different User models?") from e
        return (user, created)