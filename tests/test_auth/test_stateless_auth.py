import pytest
from unittest.mock import MagicMock

from easyjwt_auth.authentication import JWTStatelessUserAuthentication
from easyjwt_auth.exceptions import InvalidToken
from easyjwt_auth.tokens import AccessToken


@pytest.mark.django_db
class TestJWTStatelessUserAuthentication:
    def test_returns_token_user_from_valid_token(self, user):
        token = AccessToken.for_user(user)
        raw_token = str(token)

        auth = JWTStatelessUserAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}

        result = auth.authenticate(request)

        assert result is not None
        token_user, validated_token = result
        assert token_user.id == user.id
        assert token_user.is_authenticated

    def test_no_user_id_claim_raises(self):
        from easyjwt_auth.backends import TokenBackend
        from easyjwt_auth.settings import api_settings

        backend = TokenBackend(
            api_settings.ALGORITHM,
            signing_key=api_settings.SIGNING_KEY,
        )
        payload = {"token_type": "access", "exp": 9999999999, "jti": "test-jti"}
        raw_token = backend.encode(payload)

        auth = JWTStatelessUserAuthentication()
        request = MagicMock()
        request.META = {"HTTP_AUTHORIZATION": f"Bearer {raw_token}"}

        with pytest.raises(InvalidToken):
            auth.authenticate(request)

    def test_no_header_returns_none(self):
        auth = JWTStatelessUserAuthentication()
        request = MagicMock()
        request.META = {}

        assert auth.authenticate(request) is None
