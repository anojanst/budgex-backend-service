"""
Authentication endpoints: Unified OTP-based authentication
Simplified to 2 endpoints: send-otp and verify-otp
If user doesn't exist, they are automatically created on verify-otp
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.database import get_db
from app.models.otp import OTP
from app.models.user import User
from app.utils.email import send_otp_email
from app.utils.otp import create_otp_code, get_otp_expiration, hash_otp, verify_otp

router = APIRouter()
security = HTTPBearer()


# Request/Response schemas
class SendOTPRequest(BaseModel):
    email: EmailStr


class SendOTPResponse(BaseModel):
    message: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(request: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Send OTP to email address.
    Works for both registration and login - if user doesn't exist, they'll be created on verify-otp
    """
    email = request.email.lower().strip()

    # Check if user exists (for informational purposes, but don't block)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # If user exists and is inactive, block the request
    if user and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    # Generate OTP
    otp_code = create_otp_code()
    hashed_otp = hash_otp(otp_code)
    expires_at = get_otp_expiration()

    # Store OTP in database (no purpose needed - unified flow)
    otp_record = OTP(
        email=email,
        otp_code=hashed_otp,
        purpose="auth",  # Unified purpose
        expires_at=expires_at,
        is_used=False,
    )
    db.add(otp_record)
    await db.commit()

    # Send OTP via email
    email_sent = await send_otp_email(email, otp_code, "authentication")

    if not email_sent:
        # Log error but don't fail request
        pass

    return SendOTPResponse(message="OTP sent to your email address")


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP and authenticate user.
    If user doesn't exist, automatically create them.
    If user exists, log them in.
    """
    email = request.email.lower().strip()
    otp_code = request.otp

    # Find valid OTP
    result = await db.execute(
        select(OTP)
        .where(
            and_(
                OTP.email == email,
                OTP.purpose == "auth",
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow(),
            )
        )
        .order_by(OTP.created_at.desc())
    )
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    # Verify OTP
    if not verify_otp(otp_code, otp_record.otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code")

    # Check if user exists
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()

    # Create user if they don't exist
    if not user:
        user = User(
            id=uuid4(),
            email=email,
            email_verified=True,
            is_active=True,
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
    else:
        # User exists - check if active
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        # Update last login
        user.last_login_at = datetime.utcnow()

    # Mark OTP as used
    otp_record.is_used = True

    await db.commit()
    await db.refresh(user)

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "email": user.email,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
        },
    )
