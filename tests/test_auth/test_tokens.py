import pytest
from datetime import timedelta

from easyjwt_auth.tokens import AccessToken, RefreshToken, Token
from easyjwt_auth.exceptions import TokenError
from easyjwt_auth.utils import aware_utcnow


@pytest.mark.django_db
class TestToken:
    def test_token_creation(self):
        token = AccessToken()
        assert "exp" in token.payload
        assert "iat" in token.payload
        assert "jti" in token.payload
        assert token["token_type"] == "access"

    def test_token_from_existing(self, access_token):
        token = AccessToken(access_token)
        assert token is not None
        assert "user_id" in token.payload

    def test_token_str_representation(self, access_token):
        token = AccessToken(access_token)
        encoded = str(token)
        assert isinstance(encoded, str)
        assert len(encoded.split(".")) == 3

    def test_token_no_type_raises_error(self):
        class BadToken(Token):
            token_type = None
            lifetime = timedelta(minutes=5)

        with pytest.raises(TokenError, match="Cannot create token with no type or lifetime"):
            BadToken()

    def test_token_no_lifetime_raises_error(self):
        class BadToken(Token):
            token_type = "bad"
            lifetime = None

        with pytest.raises(TokenError, match="Cannot create token with no type or lifetime"):
            BadToken()


@pytest.mark.django_db
class TestAccessToken:
    def test_access_token_for_user(self, user):
        token = AccessToken.for_user(user)
        assert str(user.id) == str(token["user_id"])
        assert token["token_type"] == "access"

    def test_access_token_expiration(self, user):
        token = AccessToken.for_user(user)
        token.set_exp(from_time=aware_utcnow() - timedelta(hours=1))

        with pytest.raises(TokenError, match="Token is invalid or expired"):
            AccessToken(str(token))

    def test_access_token_invalid_raises_error(self):
        with pytest.raises(TokenError, match="Token is invalid or expired"):
            AccessToken("invalid.token.string")


@pytest.mark.django_db
class TestRefreshToken:
    def test_refresh_token_for_user(self, user):
        token = RefreshToken.for_user(user)
        assert str(user.id) == str(token["user_id"])
        assert token["token_type"] == "refresh"

    def test_refresh_token_access_property(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        assert isinstance(access, AccessToken)
        assert access["user_id"] == refresh["user_id"]
        assert access["token_type"] == "access"

    def test_refresh_token_access_expires_with_refresh(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        assert access["exp"] <= refresh["exp"]


@pytest.mark.django_db
class TestTokenVerification:
    def test_verify_token_type_correct(self, access_token):
        token = AccessToken(access_token)
        token.verify_token_type()

    def test_verify_token_type_wrong_raises(self, refresh_token):
        with pytest.raises(TokenError, match="Token has wrong type"):
            AccessToken(refresh_token).verify_token_type()

    def test_verify_expired_token_raises(self, user):
        token = AccessToken.for_user(user)
        token.set_exp(from_time=aware_utcnow() - timedelta(hours=1))

        with pytest.raises(TokenError, match="Token 'exp' claim has expired"):
            token.verify()

    def test_check_exp_missing_claim_raises(self):
        token = AccessToken()
        del token.payload["exp"]

        with pytest.raises(TokenError, match="Token has no 'exp' claim"):
            token.check_exp()
