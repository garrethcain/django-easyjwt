import pytest

from easyjwt_auth.models import TokenUser
from easyjwt_auth.tokens import AccessToken


@pytest.fixture
def token_user(user):
    token = AccessToken.for_user(user)
    return TokenUser(token)


class TestTokenUser:
    def test_id_from_user_id_claim(self, token_user, user):
        assert token_user.id == user.id

    def test_pk_matches_id(self, token_user, user):
        assert token_user.pk == user.id

    def test_is_active(self, token_user):
        assert token_user.is_active is True

    def test_is_authenticated(self, token_user):
        assert token_user.is_authenticated is True

    def test_is_not_anonymous(self, token_user):
        assert token_user.is_anonymous is False

    def test_str_representation(self, token_user, user):
        assert str(token_user) == f"TokenUser {user.id}"

    def test_username_empty_by_default(self, token_user):
        assert token_user.username == ""

    def test_is_staff_false_by_default(self, token_user):
        assert token_user.is_staff is False

    def test_is_superuser_false_by_default(self, token_user):
        assert token_user.is_superuser is False

    def test_save_raises(self, token_user):
        with pytest.raises(NotImplementedError):
            token_user.save()

    def test_delete_raises(self, token_user):
        with pytest.raises(NotImplementedError):
            token_user.delete()

    def test_set_password_raises(self, token_user):
        with pytest.raises(NotImplementedError):
            token_user.set_password("test")

    def test_check_password_raises(self, token_user):
        with pytest.raises(NotImplementedError):
            token_user.check_password("test")

    def test_equality_by_id(self, token_user, user):
        token = AccessToken.for_user(user)
        other = TokenUser(token)
        assert token_user == other

    def test_inequality_different_ids(self, token_user, inactive_user):
        token = AccessToken.for_user(inactive_user)
        other = TokenUser(token)
        assert token_user != other

    def test_hash_matches_id(self, token_user, user):
        assert hash(token_user) == hash(user.id)

    def test_no_permissions(self, token_user):
        assert token_user.get_group_permissions() == set()
        assert token_user.get_all_permissions() == set()
        assert token_user.has_perm("auth.test") is False
        assert token_user.has_perms(["auth.test"]) is False
        assert token_user.has_module_perms("auth") is False

    def test_getattr_custom_claim(self, token_user):
        assert token_user.token["user_id"] is not None
        assert token_user.nonexistent_claim is None
