import pytest

from easyjwt_user.admin import UserCreationForm


@pytest.mark.django_db
class TestUserCreationFormPasswordValidation:
    def test_weak_password_rejected(self):
        form = UserCreationForm(
            data={
                "email": "new@example.com",
                "password1": "123",
                "password2": "123",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_common_password_rejected(self):
        form = UserCreationForm(
            data={
                "email": "new@example.com",
                "password1": "password",
                "password2": "password",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors

    def test_strong_password_accepted(self):
        form = UserCreationForm(
            data={
                "email": "new@example.com",
                "password1": "S3cure!P@ssw0rd#2026",
                "password2": "S3cure!P@ssw0rd#2026",
            }
        )
        assert form.is_valid(), form.errors

    def test_mismatched_passwords_rejected(self):
        form = UserCreationForm(
            data={
                "email": "new@example.com",
                "password1": "S3cure!P@ssw0rd#2026",
                "password2": "Different!P@ssw0rd#9999",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors
        assert any("don" in str(e) and "match" in str(e) for e in form.errors["password2"])

    def test_numeric_only_password_rejected(self):
        form = UserCreationForm(
            data={
                "email": "new@example.com",
                "password1": "123456789012",
                "password2": "123456789012",
            }
        )
        assert not form.is_valid()
        assert "password2" in form.errors
