from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from rest_framework.test import APIRequestFactory

from easyjwt_auth.exceptions import TokenError
from easyjwt_auth.serializers import TokenBlacklistSerializer
from easyjwt_auth.settings import api_settings
from easyjwt_auth.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from easyjwt_auth.tokens import RefreshToken
from easyjwt_auth.utils import aware_utcnow
from easyjwt_auth.views import TokenBlacklistView


@pytest.mark.django_db
class TestOutstandingTokenModel:
    def test_str(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]
        outstanding = OutstandingToken.objects.get(jti=jti)
        assert str(outstanding) == f"Token for {user} ({jti})"

    def test_cascade_delete_with_user(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]
        assert OutstandingToken.objects.filter(jti=jti).exists()
        user.delete()
        assert not OutstandingToken.objects.filter(jti=jti).exists()


@pytest.mark.django_db
class TestBlacklistedTokenModel:
    def test_str(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()
        blacklisted = BlacklistedToken.objects.get(token__jti=token[api_settings.JTI_CLAIM])
        assert str(blacklisted) == f"Blacklisted token for {user}"

    def test_cascade_delete_with_outstanding(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()
        outstanding = OutstandingToken.objects.get(jti=token[api_settings.JTI_CLAIM])
        outstanding.delete()
        assert not BlacklistedToken.objects.exists()


@pytest.mark.django_db
class TestBlacklistMixin:
    def test_for_user_creates_outstanding_token(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]
        outstanding = OutstandingToken.objects.get(jti=jti)
        assert outstanding.user == user
        assert outstanding.token == str(token)
        assert outstanding.created_at is not None

    def test_blacklist_creates_blacklisted_token(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()

        jti = token[api_settings.JTI_CLAIM]
        outstanding = OutstandingToken.objects.get(jti=jti)
        assert BlacklistedToken.objects.filter(token=outstanding).exists()

    def test_blacklist_is_idempotent(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()
        token.blacklist()
        assert BlacklistedToken.objects.count() == 1

    def test_blacklist_creates_outstanding_if_missing(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]
        OutstandingToken.objects.filter(jti=jti).delete()
        token.blacklist()
        assert OutstandingToken.objects.filter(jti=jti).exists()

    def test_check_blacklist_passes_when_not_blacklisted(self, user):
        token = RefreshToken.for_user(user)
        token.check_blacklist()

    def test_check_blacklist_raises_when_blacklisted(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()
        with pytest.raises(TokenError, match="blacklisted"):
            RefreshToken(str(token))

    def test_verify_raises_when_blacklisted(self, user):
        token = RefreshToken.for_user(user)
        token.blacklist()
        with pytest.raises(TokenError, match="blacklisted"):
            RefreshToken(str(token))


@pytest.mark.django_db
class TestTokenBlacklistSerializer:
    def test_blacklists_valid_refresh_token(self, user):
        token = RefreshToken.for_user(user)
        serializer = TokenBlacklistSerializer(data={"refresh": str(token)})
        assert serializer.is_valid()
        assert BlacklistedToken.objects.filter(token__jti=token[api_settings.JTI_CLAIM]).exists()

    def test_invalid_token_raises_token_error(self):
        serializer = TokenBlacklistSerializer(data={"refresh": "invalid.token"})
        with pytest.raises(TokenError):
            serializer.is_valid()


@pytest.mark.django_db
class TestTokenBlacklistView:
    def test_post_valid_refresh_returns_200(self, user):
        token = RefreshToken.for_user(user)
        factory = APIRequestFactory()
        request = factory.post("/", {"refresh": str(token)}, format="json")
        response = TokenBlacklistView.as_view()(request)
        assert response.status_code == 200

    def test_post_invalid_token_returns_401(self):
        factory = APIRequestFactory()
        request = factory.post("/", {"refresh": "invalid.token"}, format="json")
        response = TokenBlacklistView.as_view()(request)
        assert response.status_code == 401

    def test_post_missing_token_returns_400(self):
        factory = APIRequestFactory()
        request = factory.post("/", {}, format="json")
        response = TokenBlacklistView.as_view()(request)
        assert response.status_code == 400


@pytest.mark.django_db
class TestFlushExpiredTokensCommand:
    def test_deletes_expired_tokens(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]
        outstanding = OutstandingToken.objects.get(jti=jti)
        outstanding.expires_at = aware_utcnow() - timedelta(seconds=1)
        outstanding.save()

        call_command("flushexpiredtokens", stdout=StringIO())
        assert not OutstandingToken.objects.filter(jti=jti).exists()

    def test_keeps_valid_tokens(self, user):
        token = RefreshToken.for_user(user)
        jti = token[api_settings.JTI_CLAIM]

        call_command("flushexpiredtokens", stdout=StringIO())
        assert OutstandingToken.objects.filter(jti=jti).exists()

    def test_deletes_only_expired(self, user):
        token1 = RefreshToken.for_user(user)
        token2 = RefreshToken.for_user(user)
        jti1 = token1[api_settings.JTI_CLAIM]
        jti2 = token2[api_settings.JTI_CLAIM]

        outstanding1 = OutstandingToken.objects.get(jti=jti1)
        outstanding1.expires_at = aware_utcnow() - timedelta(seconds=1)
        outstanding1.save()

        call_command("flushexpiredtokens", stdout=StringIO())
        assert not OutstandingToken.objects.filter(jti=jti1).exists()
        assert OutstandingToken.objects.filter(jti=jti2).exists()
