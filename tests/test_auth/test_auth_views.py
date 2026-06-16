import pytest
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from easyjwt_auth.views import CreateUserView, PasswordChangeView


@pytest.mark.django_db
class TestCreateUserView:
    def test_post_valid_data_creates_user(self):
        url = reverse("create_user")
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {
                "email": "newuser@example.com",
                "password": "S3cure!P@ssw0rd#2026",
            },
            format="json",
        )
        response = CreateUserView.as_view()(request)
        assert response.status_code == 201
        assert response.data["email"] == "newuser@example.com"

    def test_post_missing_data_returns_400(self):
        url = reverse("create_user")
        factory = APIRequestFactory()
        request = factory.post("/", {}, format="json")
        response = CreateUserView.as_view()(request)
        assert response.status_code == 400

    def test_post_weak_password_returns_400(self):
        url = reverse("create_user")
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {"email": "newuser@example.com", "password": "123"},
            format="json",
        )
        response = CreateUserView.as_view()(request)
        assert response.status_code == 400

    def test_post_duplicate_email_returns_400(self, user):
        url = reverse("create_user")
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {"email": user.email, "password": "S3cure!P@ssw0rd#2026"},
            format="json",
        )
        response = CreateUserView.as_view()(request)
        assert response.status_code == 400


@pytest.mark.django_db
class TestAuthPasswordChangeView:
    def test_post_valid_credentials_returns_200(self, user):
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {
                "email": "test@example.com",
                "password": "testpass123",
                "new_password": "N3wP@ssw0rd!2026",
            },
            format="json",
        )
        response = PasswordChangeView.as_view()(request)
        assert response.status_code == 200

    def test_post_invalid_credentials_returns_400(self, user):
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {
                "email": "test@example.com",
                "password": "wrongpass",
                "new_password": "N3wP@ssw0rd!2026",
            },
            format="json",
        )
        response = PasswordChangeView.as_view()(request)
        assert response.status_code == 400

    def test_post_missing_data_returns_400(self):
        factory = APIRequestFactory()
        request = factory.post("/", {}, format="json")
        response = PasswordChangeView.as_view()(request)
        assert response.status_code == 400

    def test_post_weak_new_password_returns_400(self, user):
        factory = APIRequestFactory()
        request = factory.post(
            "/",
            {
                "email": "test@example.com",
                "password": "testpass123",
                "new_password": "123",
            },
            format="json",
        )
        response = PasswordChangeView.as_view()(request)
        assert response.status_code == 400
