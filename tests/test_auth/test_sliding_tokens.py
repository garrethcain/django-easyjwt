import pytest
from rest_framework.test import APIRequestFactory

from easyjwt_auth.exceptions import TokenError
from easyjwt_auth.serializers import (
    TokenObtainSlidingSerializer,
    TokenRefreshSlidingSerializer,
)
from easyjwt_auth.tokens import SlidingToken
from easyjwt_auth.views import TokenObtainSlidingView, TokenRefreshSlidingView


@pytest.mark.django_db
class TestSlidingToken:
    def test_token_creation(self):
        token = SlidingToken()
        assert token["token_type"] == "sliding"
        assert "exp" in token
        assert "refresh_exp" in token

    def test_refresh_exp_is_set(self):
        token = SlidingToken()
        assert token["refresh_exp"] > token["exp"]

    def test_for_user(self, user):
        token = SlidingToken.for_user(user)
        assert token["user_id"] == user.id
        assert token["token_type"] == "sliding"


@pytest.mark.django_db
class TestTokenObtainSlidingSerializer:
    def test_valid_credentials_returns_sliding_token(self, user, user_credentials):
        from django.contrib.auth import authenticate
        from rest_framework.exceptions import ValidationError

        serializer = TokenObtainSlidingSerializer(data=user_credentials)
        serializer.is_valid()

    def test_invalid_credentials_raises(self):
        from rest_framework.exceptions import AuthenticationFailed

        serializer = TokenObtainSlidingSerializer(
            data={"email": "wrong@example.com", "password": "wrongpass"}
        )
        with pytest.raises(AuthenticationFailed):
            serializer.is_valid()


@pytest.mark.django_db
class TestTokenRefreshSlidingSerializer:
    def test_valid_token_returns_refreshed_token(self, user):
        token = SlidingToken.for_user(user)
        serializer = TokenRefreshSlidingSerializer(data={"token": str(token)})
        assert serializer.is_valid()
        assert "token" in serializer.validated_data

    def test_invalid_token_raises(self):
        serializer = TokenRefreshSlidingSerializer(data={"token": "invalid.token"})
        with pytest.raises(TokenError):
            serializer.is_valid()


@pytest.mark.django_db
class TestTokenObtainSlidingView:
    def test_post_valid_credentials_returns_token(self, user, user_credentials):
        factory = APIRequestFactory()
        request = factory.post("/", user_credentials, format="json")
        response = TokenObtainSlidingView.as_view()(request)
        assert response.status_code == 200
        assert "token" in response.data

    def test_post_invalid_credentials_returns_401(self):
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {"email": "wrong@example.com", "password": "wrongpass"},
            format="json",
        )
        response = TokenObtainSlidingView.as_view()(request)
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefreshSlidingView:
    def test_post_valid_token_returns_new_token(self, user):
        token = SlidingToken.for_user(user)
        factory = APIRequestFactory()
        request = factory.post("/", {"token": str(token)}, format="json")
        response = TokenRefreshSlidingView.as_view()(request)
        assert response.status_code == 200
        assert "token" in response.data

    def test_post_invalid_token_returns_401(self):
        factory = APIRequestFactory()
        request = factory.post("/", {"token": "invalid.token"}, format="json")
        response = TokenRefreshSlidingView.as_view()(request)
        assert response.status_code == 401
