import json
import requests
from typing import Tuple

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from rest_framework import authentication, exceptions, HTTP_HEADER_ENCODING

from .settings import api_settings
from .utils import TokenManager

__all__ = [
    "RemoteAuthBackend",
    "EasyJWTAuthentication",
]

User = get_user_model()


class RemoteAuthBackend(BaseBackend):
    """
    Django authentication backend that delegates credential checking
    to a remote easyjwt_auth server.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        tokenmanager = TokenManager()
        try:
            tokenmanager.authenticate(
                create_local_user=True, **{User.USERNAME_FIELD: username, "password": password}
            )
            return self._get_user_by_kwargs(username)
        except exceptions.AuthenticationFailed:
            pass
        return None

    def _get_user_by_kwargs(self, username: str):
        """Used here to get a user by the USER_ID_FIELD in the settings"""
        try:
            user = User.objects.get(**{User.USERNAME_FIELD: username})
        except User.DoesNotExist:
            user = None
        return user

    def get_user(self, user_id: int):
        """Used by a view to rerieve a user object by pk for an already authenticated user"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class EasyJWTAuthentication(authentication.BaseAuthentication):
    def __verify_token(self, jwt: str) -> Tuple[bool, dict]:
        root_url = api_settings.REMOTE_AUTH_SERVICE_URL
        path = api_settings.REMOTE_AUTH_SERVICE_VERIFY_PATH
        timeout = api_settings.REMOTE_AUTH_REQUEST_TIMEOUT
        ssl_verify = api_settings.REMOTE_AUTH_SSL_VERIFY
        headers = {
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                f"{root_url}{path}",
                data=json.dumps({"token": jwt}),
                headers=headers,
                timeout=timeout,
                verify=ssl_verify,
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            TokenManager._handle_request_error(e)

        content_type = response.headers.get("Content-Type")
        if content_type != "application/json":
            raise exceptions.AuthenticationFailed(
                f"Authentication Service response has incorrect content-type. "
                f"Expected application/json but received {content_type}"
            )

        if response.status_code != 200:
            try:
                return (False, response.json())
            except ValueError:
                return (False, {"detail": "Token is invalid or expired"})

        return (True, {})

    def __get_authorization_header(self, request):
        """
        Return request's 'Authorization:' header, as a bytestring.

        Hide some test client ickyness where the header can be unicode.
        """
        auth = request.headers.get("Authorization")
        if isinstance(auth, str):
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth.decode("utf-8") if auth else None

    def authenticate(self, request):
        """
        Validates a JWT against a remote authentication service.
        """
        auth_header = self.__get_authorization_header(request)

        if auth_header is None:
            return None
        elif len(auth_header.split(" ")) == 1:
            msg = "Invalid basic header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header.split(" ")) > 2:
            msg = "Invalid basic header. Credentials string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)
        try:
            auth_method, auth_string = auth_header.split(" ", 1)
            auth_string = auth_string.strip()
        except ValueError as e:
            msg = "Malformed Authorization Header"
            raise exceptions.AuthenticationFailed(msg) from e

        if auth_method not in api_settings.AUTH_HEADER_TYPES:
            return None

        token_verified, message = self.__verify_token(jwt=auth_string)
        if not token_verified:
            raise exceptions.AuthenticationFailed(message.get("detail"))

        token_manager = TokenManager()
        user, _ = token_manager._create_or_update_user(auth_string)
        return (user, None)

    def authenticate_header(self, request):
        return api_settings.AUTH_HEADER_TYPES[0]
