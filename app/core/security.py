"""
Security utilities: JWT, OTP generation/validation
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password context (for future password hashing)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Dictionary containing user data (e.g., {"sub": user_id, "email": email})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_otp(length: int = None) -> str:
    """
    Generate random OTP code

    Args:
        length: Length of OTP (defaults to settings.OTP_LENGTH)

    Returns:
        Random numeric OTP string
    """
    import secrets

    if length is None:
        length = settings.OTP_LENGTH

    # Generate random number with specified length
    otp = ""
    for _ in range(length):
        otp += str(secrets.randbelow(10))

    return otp


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    (For future use if password authentication is added)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    (For future use if password authentication is added)
    """
    return pwd_context.verify(plain_password, hashed_password)
