from app.security.token_auth import TokenAuthenticator


def test_encrypt_and_verify_roundtrip():
    auth = TokenAuthenticator("test_secret_key_12345678901234")
    token = auth.encrypt_token("client_1", "session_abc")
    result = auth.verify_token(token)
    assert result is not None
    assert result.client_id == "client_1"
    assert result.session_id == "session_abc"


def test_tampered_token_is_rejected():
    auth = TokenAuthenticator("test_secret_key_12345678901234")
    token = auth.encrypt_token("client_1", "session_abc")
    tampered = token[:-2] + "xx"
    assert auth.verify_token(tampered) is None


def test_invalid_format_returns_none():
    auth = TokenAuthenticator("test_secret_key_12345678901234")
    assert auth.verify_token("not-a-valid-token") is None
