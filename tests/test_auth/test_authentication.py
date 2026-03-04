import pytest
from unittest.mock import MagicMock

from rest_framework import exceptions
from easyjwt_auth.authentication import JWTAuthentication
from easyjwt_auth.exceptions import InvalidToken, AuthenticationFailed


@pytest.mark.django_db
class TestJWTAuthentication:
    def test_authenticate_valid_token(self, user, access_token):
        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}
        request.headers = {"Authorization": f"Bearer {access_token}"}

        result = auth.authenticate(request)

        assert result is not None
        authenticated_user, validated_token = result
        assert authenticated_user.email == user.email
        assert authenticated_user.id == user.id

    def test_authenticate_no_header_returns_none(self):
        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {}
        request.headers = {}

        result = auth.authenticate(request)

        assert result is None

    def test_authenticate_invalid_header_format_raises(self):
        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": "InvalidFormat"}
        request.headers = {"Authorization": "InvalidFormat"}

        result = auth.authenticate(request)

        assert result is None

    def test_authenticate_invalid_token_raises(self):
        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer invalid.token.here"}
        request.headers = {"Authorization": "Bearer invalid.token.here"}

        with pytest.raises((InvalidToken, exceptions.AuthenticationFailed)):
            auth.authenticate(request)

    def test_authenticate_user_not_found_raises(self):
        from easyjwt_auth.tokens import AccessToken

        fake_token = AccessToken()
        fake_token["user_id"] = 999999

        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {str(fake_token)}"}
        request.headers = {"Authorization": f"Bearer {str(fake_token)}"}

        with pytest.raises(AuthenticationFailed, match="User not found"):
            auth.authenticate(request)

    def test_authenticate_inactive_user_raises(self, inactive_user):
        from easyjwt_auth.tokens import AccessToken

        token = AccessToken.for_user(inactive_user)

        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}
        request.headers = {"Authorization": f"Bearer {str(token)}"}

        with pytest.raises(AuthenticationFailed, match="User is inactive"):
            auth.authenticate(request)

    def test_get_header_encoding(self):
        auth = JWTAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": "Bearer token123"}

        header = auth.get_header(request)

        assert isinstance(header, bytes)
        assert header == b"Bearer token123"

    def test_get_raw_token_extraction(self):
        auth = JWTAuthentication()
        header = b"Bearer token123"

        raw_token = auth.get_raw_token(header)

        assert raw_token == b"token123"

    def test_authenticate_header_returns_correct_format(self):
        auth = JWTAuthentication()
        request = MagicMock()

        header = auth.authenticate_header(request)

        assert "Bearer" in header
