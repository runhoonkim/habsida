from auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password
)

def test_hash_is_not_the_plain_password():
    """
    Test that the hash_password function does not return the plain password.
    """
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_verify_password_accepts_correct_and_rejects_wrong():
    """
    Test that verify_password correctly accepts the correct password and rejects a wrong one.
    """
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) 
    assert not verify_password("wrong", hashed)

def test_token_round_trip():
    """
    Test that a token can be created and then decoded to retrieve the original data.
    """
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42

def test_garbage_token_decodes_to_none():
    """
    Test that decoding a garbage token returns None.
    """
    assert decode_access_token("not-a-jwt") is None