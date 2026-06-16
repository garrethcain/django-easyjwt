import pytest
import responses as responses_mock
from django.test import RequestFactory
from rest_framework.test import APIClient

from easyjwt_client.views import PasswordChangeView


@pytest.fixture
def client_urls(settings):
    settings.ROOT_URLCONF = "tests.test_client.urls"


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenObtainPairView:
    def test_valid_credentials_returns_tokens(self, user, user_credentials):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/",
                json={"access": "test_access", "refresh": "test_refresh"},
                status=200,
            )
            rsps.add(
                responses_mock.GET,
                "http://remote-auth.test/auth/user/",
                json={
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/", user_credentials)

            assert response.status_code == 200
            data = response.json()
            assert "access" in data
            assert "refresh" in data

    def test_missing_data_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenRefreshView:
    def test_valid_refresh_returns_new_access(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/refresh/",
                json={"access": "new_access_token"},
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/refresh/", {"refresh": "old_refresh_token"})

            assert response.status_code == 200
            assert "access" in response.json()

    def test_missing_refresh_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/refresh/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestTokenVerifyView:
    def test_valid_token_returns_200(self):
        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/token/verify/",
                json={},
                status=200,
            )

            client = APIClient()
            response = client.post("/auth/token/verify/", {"token": "some_token"})

            assert response.status_code == 200

    def test_missing_token_returns_400(self):
        client = APIClient()
        response = client.post("/auth/token/verify/", {})

        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.usefixtures("client_urls")
class TestPasswordChangeView:
    def test_matching_passwords_succeed(self, user):
        factory = RequestFactory()
        request = factory.post(
            "/auth/password-change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpass123",
                "new_password2": "newpass123",
            },
        )
        request.user = user

        with responses_mock.RequestsMock() as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/password-change/",
                json={"detail": "Password changed successfully."},
                status=200,
            )

            view = PasswordChangeView()
            view.request = request
            view.kwargs = {}
            response = view.post(request)

            assert response.status_code == 302

    @pytest.mark.xfail(
        reason="SEC-1: new_password2 is never validated in PasswordChangeView.post",
        strict=True,
    )
    def test_mismatched_passwords_are_rejected(self, user):
        """SEC-1: mismatched new passwords should NOT trigger a remote password change."""
        factory = RequestFactory()
        request = factory.post(
            "/auth/password-change/",
            {
                "old_password": "testpass123",
                "new_password1": "newpass123",
                "new_password2": "different456",
            },
        )
        request.user = user

        with responses_mock.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            rsps.add(
                responses_mock.POST,
                "http://remote-auth.test/auth/password-change/",
                json={},
                status=200,
            )

            view = PasswordChangeView()
            view.request = request
            view.kwargs = {}
            response = view.post(request)

            assert response.status_code != 302
