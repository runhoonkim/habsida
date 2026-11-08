from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(plain: str) -> str:
    """
    Hash a plaintext password using the configured password context.

    Args:
        plain: The plaintext password to hash.

    Returns:
        The encoded password hash for storage.
    """
    return pwd_context.hash(plain)


def verify_password(
    plain: str,
    hashed: str,
) -> bool:
    """
    Check a plaintext password against a stored password hash.

    Args:
        plain: The plaintext password to check.
        hashed: The stored password hash.

    Returns:
        True if the password matches the hash; otherwise, False.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT access token identifying a user.

    The token includes
        the user ID as the subject ("sub") 
        the token type set as "access"
        and an expiration ("exp") based on ACCESS_TOKEN_EXPIRE_MINUTES.

    Args:
        user_id: The ID of the user the token identifies.

    Returns:
        A JWT signed with SECRET_KEY using ALGORITHM.
    """
    access_expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "token_type": "access",
        "exp": access_expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

def create_refresh_token(user_id: int) -> str:
    """
    Create a signed JWT refresh token identifying a user.
    
        The token includes
            the user ID as the subject ("sub") 
            the token type set as "refresh"
            and an expiration ("exp") based on REFRESH_TOKEN_EXPIRE_DAYS.
    
        Args:
            user_id: The ID of the user the token identifies.
    
        Returns:
            A JWT signed with SECRET_KEY using ALGORITHM.
    """
    refresh_expire = (
        datetime.now(timezone.utc)
        + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload = {
        "sub": str(user_id),
        "token_type": "refresh",
        "exp": refresh_expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

def decode_access_token(token: str) -> int | None:
    """
    Validate a JWT access token and extract its user ID.

    Checks the signature and validates claims, including expiration
    when present, using SECRET_KEY and the allowed ALGORITHM.

    Args:
        token: The encoded JWT access token.

    Returns:
        The integer user ID from the subject ("sub"), or None if JWT
        validation fails, the subject is missing, or its value cannot
        be parsed as an integer.
    """
    try:
        payload = jwt.decode(
            token=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,
                "require_sub": True,
            },
        )

        if payload.get("token_type") != "access":
            return None
        
        return int(payload["sub"])

    except (JWTError, KeyError, ValueError):
        return None

def decode_refresh_token(token: str) -> int | None:
    """
    Validate a JWT refresh token and extract its user ID.

    Checks the signature and validates claims, including expiration
    when present, using SECRET_KEY and the allowed ALGORITHM.

    Args:
        token: The encoded JWT access token.

    Returns:
        The integer user ID from the subject ("sub"), or None if JWT
        validation fails, the subject is missing, or its value cannot
        be parsed as an integer.
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,
                "require_sub": True,
            }
        )

        if payload.get("token_type") != "refresh":
            return None
        
        return int(payload["sub"])
    
    except (JWTError, KeyError, ValueError):
        return None