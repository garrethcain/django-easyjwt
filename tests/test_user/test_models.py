import pytest

from easyjwt_user.models import User


@pytest.mark.django_db
class TestUserManager:
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

        assert user.pk is not None
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_lowercases_email(self):
        user = User.objects.create_user(
            email="Test.User@EXAMPLE.COM",
            password="testpass123",
        )

        assert user.email == "test.user@example.com"

    def test_create_user_without_email_raises(self):
        with pytest.raises(ValueError, match="email must be set"):
            User.objects.create_user(email="", password="testpass123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

        assert user.pk is not None
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active

    def test_create_superuser_without_staff_raises(self):
        with pytest.raises(ValueError, match="is_staff=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_staff=False,
            )

    def test_create_superuser_without_superuser_raises(self):
        with pytest.raises(ValueError, match="is_superuser=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_superuser=False,
            )

    def test_create_superuser_without_active_raises_correct_message(self):
        with pytest.raises(ValueError, match="is_active=True"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="adminpass123",
                is_active=False,
            )
