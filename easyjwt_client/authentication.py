import json
import requests
from typing import Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions, HTTP_HEADER_ENCODING

from .utils import TokenManager

User = get_user_model()


class RemoteAuthBackend(authentication.BaseAuthentication):
    """
    Allows views to authenticate against the remote backend.
    These two classes have been kept seperate on purpose.
    """

    def authenticate(self, request, username: str, password: str):
        """
        Override the authentication method to allow auth to collect
        a user from the remote authentication service.
        """
        tokenmanager = TokenManager()
        try:
            _ = tokenmanager.authenticate(
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
        root_url = settings.EASY_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_VERIFY_PATH"]
        timeout = settings.EASY_JWT.get("REMOTE_AUTH_REQUEST_TIMEOUT", 30)
        ssl_verify = settings.EASY_JWT.get("REMOTE_AUTH_SSL_VERIFY", True)
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
            return (False, response.json())

        return (True, {})

    def __get_user_details(self, jwt: str) -> dict:
        auth_header_types = settings.EASY_JWT["AUTH_HEADER_TYPES"]
        root_url = settings.EASY_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.EASY_JWT["REMOTE_AUTH_SERVICE_USER_PATH"]
        timeout = settings.EASY_JWT.get("REMOTE_AUTH_REQUEST_TIMEOUT", 30)
        ssl_verify = settings.EASY_JWT.get("REMOTE_AUTH_SSL_VERIFY", True)
        headers: dict[str, str] = {
            "Authorization": f"{auth_header_types[0]} {jwt}",
            "content-type": "application/json",
        }

        request = requests.Request("GET", f"{root_url}{path}", data={}, headers=headers)
        prepped = request.prepare()
        prepped.headers.update(headers)

        with requests.Session() as session:
            try:
                response = session.send(prepped, timeout=timeout, verify=ssl_verify)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                TokenManager._handle_request_error(e)

        if response.status_code != 200:
            raise exceptions.AuthenticationFailed(response.json())
        return json.loads(response.text)

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

        if auth_method not in settings.EASY_JWT["AUTH_HEADER_TYPES"]:
            return None

        token_verified, message = self.__verify_token(jwt=auth_string)
        if not token_verified:
            raise exceptions.AuthenticationFailed(message.get("detail"))

        token_manager = TokenManager()
        user, _ = token_manager._create_or_update_user(auth_string)
        return (user, None)

    def authenticate_header(self, request):
        return "JWT"
