"""
OTP utility functions for generation, validation, and storage
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_otp


def hash_otp(otp: str) -> str:
    """
    Hash OTP before storing in database using SHA256

    Args:
        otp: Plain OTP string

    Returns:
        Hashed OTP string (format: salt:hash)
    """
    # Use SHA256 for OTP hashing (OTPs are short-lived, so this is sufficient)
    # Add a salt to prevent rainbow table attacks
    salt = secrets.token_hex(16)  # 32 character hex string
    hash_obj = hashlib.sha256()
    hash_obj.update((salt + otp).encode("utf-8"))
    hashed = hash_obj.hexdigest()
    # Store as salt:hash for verification
    return f"{salt}:{hashed}"


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """
    Verify OTP against stored hash

    Args:
        plain_otp: Plain OTP string from user
        hashed_otp: Hashed OTP from database (format: salt:hash)

    Returns:
        True if OTP matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, stored_hash = hashed_otp.split(":", 1)
        # Recompute hash with same salt
        hash_obj = hashlib.sha256()
        hash_obj.update((salt + plain_otp).encode("utf-8"))
        computed_hash = hash_obj.hexdigest()
        # Compare using constant-time comparison to prevent timing attacks
        return secrets.compare_digest(computed_hash, stored_hash)
    except (ValueError, AttributeError):
        # Invalid format or None
        return False


def create_otp_code() -> str:
    """
    Generate a new OTP code

    Returns:
        Random numeric OTP string
    """
    return generate_otp(settings.OTP_LENGTH)


def get_otp_expiration() -> datetime:
    """
    Get expiration datetime for OTP

    Returns:
        Datetime when OTP expires
    """
    return datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)


def is_otp_expired(expires_at: datetime) -> bool:
    """
    Check if OTP has expired

    Args:
        expires_at: Expiration datetime

    Returns:
        True if expired, False otherwise
    """
    return datetime.utcnow() > expires_at


async def cleanup_expired_otps(db: AsyncSession) -> int:
    """
    Clean up expired OTPs from database

    Args:
        db: Database session

    Returns:
        Number of deleted OTPs
    """
    from app.models.otp import OTP

    result = await db.execute(delete(OTP).where(OTP.expires_at < datetime.utcnow()))
    await db.commit()
    return result.rowcount
