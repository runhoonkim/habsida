from auth import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_is_not_the_plain_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_verify_password_accepts_correct_and_rejects_wrong():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_round_trip():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_garbage_token_decodes_to_none():
    assert decode_access_token("not-a-jwt") is None
