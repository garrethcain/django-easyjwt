from datetime import timedelta

import pytest

from easyjwt_auth.backends import TokenBackend
from easyjwt_auth.exceptions import TokenBackendError


class TestTokenBackend:
    def test_encode_decode_round_trip(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!")
        payload = {"user_id": 1, "exp": 9999999999}
        encoded = backend.encode(payload)
        decoded = backend.decode(encoded)
        assert decoded["user_id"] == 1

    def test_invalid_algorithm_raises(self):
        with pytest.raises(TokenBackendError, match="Unrecognized algorithm"):
            TokenBackend("INVALID")

    def test_decode_invalid_token_raises(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!")
        with pytest.raises(TokenBackendError):
            backend.decode("invalid.token.here")

    def test_decode_wrong_key_raises(self):
        backend_encode = TokenBackend("HS256", signing_key="test-signing-key-a-at-least-32-bytes-long!")
        backend_decode = TokenBackend("HS256", signing_key="test-signing-key-b-at-least-32-bytes-long!")
        encoded = backend_encode.encode({"exp": 9999999999})
        with pytest.raises(TokenBackendError):
            backend_decode.decode(encoded)


class TestTokenBackendAudience:
    def test_audience_encoded_and_validated(self):
        backend = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", audience="my-audience"
        )
        encoded = backend.encode({"exp": 9999999999})
        decoded = backend.decode(encoded)
        assert decoded["aud"] == "my-audience"

    def test_wrong_audience_raises(self):
        backend_encode = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", audience="aud-a"
        )
        backend_decode = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", audience="aud-b"
        )
        encoded = backend_encode.encode({"exp": 9999999999})
        with pytest.raises(TokenBackendError):
            backend_decode.decode(encoded)

    def test_no_audience_no_verification(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!")
        encoded = backend.encode({"exp": 9999999999})
        decoded = backend.decode(encoded)
        assert "aud" not in decoded


class TestTokenBackendIssuer:
    def test_issuer_encoded_and_validated(self):
        backend = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", issuer="my-issuer"
        )
        encoded = backend.encode({"exp": 9999999999})
        decoded = backend.decode(encoded)
        assert decoded["iss"] == "my-issuer"

    def test_wrong_issuer_raises(self):
        backend_encode = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", issuer="iss-a"
        )
        backend_decode = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", issuer="iss-b"
        )
        encoded = backend_encode.encode({"exp": 9999999999})
        with pytest.raises(TokenBackendError):
            backend_decode.decode(encoded)


class TestTokenBackendLeeway:
    def test_leeway_allows_slightly_expired_token(self):
        from easyjwt_auth.utils import aware_utcnow, datetime_from_epoch

        now = aware_utcnow()
        exp_timestamp = int((now - timedelta(seconds=5)).timestamp())
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", leeway=60)
        encoded = backend.encode({"exp": exp_timestamp})
        decoded = backend.decode(encoded)
        assert decoded["exp"] == exp_timestamp

    def test_leeway_int(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", leeway=30)
        assert backend.get_leeway() == timedelta(seconds=30)

    def test_leeway_float(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", leeway=1.5)
        assert backend.get_leeway() == timedelta(seconds=1.5)

    def test_leeway_timedelta(self):
        backend = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", leeway=timedelta(seconds=45)
        )
        assert backend.get_leeway() == timedelta(seconds=45)

    def test_leeway_none_is_zero(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!")
        assert backend.get_leeway() == timedelta(seconds=0)

    def test_leeway_invalid_type_raises(self):
        backend = TokenBackend(
            "HS256", signing_key="test-signing-key-at-least-32-bytes-long!!", leeway="invalid"
        )
        with pytest.raises(TokenBackendError, match="Unrecognized type"):
            backend.get_leeway()


class TestTokenBackendVerifyFalse:
    def test_decode_without_verification(self):
        backend = TokenBackend("HS256", signing_key="test-signing-key-at-least-32-bytes-long!!")
        encoded = backend.encode({"exp": 9999999999, "custom": "data"})
        decoded = backend.decode(encoded, verify=False)
        assert decoded["custom"] == "data"
