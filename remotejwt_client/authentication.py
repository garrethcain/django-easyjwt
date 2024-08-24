import json
import requests
from typing import Tuple
from base64 import b64decode

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions, HTTP_HEADER_ENCODING

from .utils import TokenManager

User = get_user_model()


class ModelBackend(authentication.BaseAuthentication):
    """
    Allows views to authenticate against the remote backend.
    These two classes have been kept seperate on purpose.
    """

    def authenticate(self, request, username=None, password=None):
        """
        Override the authentication method to allow auth to collect
        a user from the remote authentication service.
        """
        tokenmanager = TokenManager()
        try:
            _ = tokenmanager.authenticate(email=username, password=password)
            return self._get_user_by_username(username=username)
        except exceptions.AuthenticationFailed as e:
            print("Authentication exception:", e)
        return None

    def _get_user_by_id(self, user_id):
        try:
            return User.object.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _get_user_by_username(self, username):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = None
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class RemoteJWTAuthentication(authentication.BaseAuthentication):
    def __verify_token(self, jwt: str) -> Tuple[bool, dict]:
        root_url = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_VERIFY_PATH"]
        headers = {
            "content-type": "application/json",
        }
        resp_code = 200
        resp_dict = {}

        try:
            response = requests.post(
                f"{root_url}{path}",
                data=json.dumps({"token": jwt}),
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

        content_type = response.headers.get("Content-Type")
        if content_type != "application/json":
            raise exceptions.AuthenticationFailed(
                f"Authentication Service response has incorrect content-type. Expected application/json but received {content_type}"
            )

        # TODO: Fix this up.
        if response.status_code != 200:
            resp_code = response.status_code
            resp_dict = response.json()

        return (resp_code == 200, resp_dict)

    def __parse_auth_string(self, auth_string: str) -> Tuple[dict, dict, str]:
        header, payload, signature = auth_string.split(".")
        header_str = b64decode(header)
        payload_str = b64decode(f"{payload}==")  # add padding back on.
        # signature = b64decode(f"{signature}==")
        return (json.loads(header_str), json.loads(payload_str), signature)

    def __get_user_details(self, user_id: int, jwt: str) -> dict:
        auth_header_types = settings.REMOTE_JWT["AUTH_HEADER_TYPES"]
        root_url = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_URL"]
        path = settings.REMOTE_JWT["REMOTE_AUTH_SERVICE_USER_PATH"].format(
            user_id=user_id
        )
        headers: dict[str, str] = {
            "Authorization": f"{auth_header_types[0]} {jwt}",
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
        return json.loads(response.text)

    def __get_authorization_header(self, request):
        """
        Return request's 'Authorization:' header, as a bytestring.

        Hide some test client ickyness where the header can be unicode.
        """
        ## The below will only see the Authorization header.
        # auth = request.META.get(settings.REMOTE_JWT["AUTH_HEADER_NAME"], b'')
        # auth = request.headers.get(settings.REMOTE_JWT["AUTH_HEADER_NAME"], b'')
        auth = request.headers.get("Authorization")
        if isinstance(auth, str):
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth.decode("utf-8") if auth else None

    def authenticate(self, request):
        """
        Validates a JWT against a remote authentication service.
        """
        # Is the user trying to actually use the HTTP Authorization header?
        auth_header = self.__get_authorization_header(request)

        if auth_header is None:
            # Might not be a request for this service.
            return None
        elif len(auth_header.split(" ")) == 1:
            msg = "Invalid basic header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header.split(" ")) > 2:
            msg = "Invalid basic header. Credentials string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)
        # Except the case where the auth string is malformed, doesn't fit into the form <Method> <String>
        try:
            auth_method, auth_string = auth_header.split(":")
            auth_string = auth_string.strip()
        except ValueError as e:
            msg = "Malformed Authorization Header"
            raise exceptions.AuthenticationFailed(msg) from e

        # If they successfully specified a method but its not AUTH_HEADER_TYPE, pass
        # through, could be Basic auth or similar
        if auth_method not in settings.REMOTE_JWT["AUTH_HEADER_TYPES"]:
            return None

        token_verified, message = self.__verify_token(jwt=auth_string)
        if not token_verified:
            raise exceptions.AuthenticationFailed(message.get("detail"))

        # If we made it this far, we're legal. Let's see if we exist in the DB.
        header_dict, payload_dict, signature = self.__parse_auth_string(auth_string)
        # We can trust the user id because we validated the signature against the remote
        # auth service to show it wasn't tampered with.
        user_id = payload_dict[settings.REMOTE_JWT["USER_ID_CLAIM"]]
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as e:
            print("User does not exist:", str(e))
            user_details = self.__get_user_details(user_id, auth_string)
            user = User.objects.create(**user_details)
        return (user, None)

    def authenticate_header(self, request):
        return "JWT"
