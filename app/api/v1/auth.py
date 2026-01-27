"""
Authentication endpoints: Registration and Login with OTP
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from uuid import uuid4

from app.database import get_db
from app.models.user import User
from app.models.otp import OTP
from app.core.security import create_access_token
from app.utils.otp import (
    create_otp_code,
    hash_otp,
    verify_otp,
    get_otp_expiration,
    is_otp_expired,
)
from app.utils.email import send_otp_email
from pydantic import BaseModel, EmailStr

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


@router.post("/register/send-otp", response_model=SendOTPResponse)
async def send_registration_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send OTP for user registration
    """
    email = request.email.lower().strip()
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate OTP
    otp_code = create_otp_code()
    hashed_otp = hash_otp(otp_code)
    expires_at = get_otp_expiration()
    
    # Store OTP in database
    otp_record = OTP(
        email=email,
        otp_code=hashed_otp,
        purpose="registration",
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    await db.commit()
    
    # Send OTP via email
    email_sent = await send_otp_email(email, otp_code, "registration")
    
    if not email_sent:
        # Don't fail the request if email fails, but log it
        # In production, you might want to handle this differently
        pass
    
    return SendOTPResponse(
        message="OTP sent to your email address"
    )


@router.post("/register/verify-otp", response_model=TokenResponse)
async def verify_registration_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and create new user account
    """
    email = request.email.lower().strip()
    otp_code = request.otp
    
    # Find valid OTP
    result = await db.execute(
        select(OTP).where(
            and_(
                OTP.email == email,
                OTP.purpose == "registration",
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            )
        ).order_by(OTP.created_at.desc())
    )
    otp_record = result.scalar_one_or_none()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Verify OTP
    if not verify_otp(otp_code, otp_record.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Check if user already exists (race condition check)
    user_result = await db.execute(select(User).where(User.email == email))
    existing_user = user_result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    new_user = User(
        id=uuid4(),
        email=email,
        email_verified=True,
        is_active=True,
        last_login_at=datetime.utcnow()
    )
    db.add(new_user)
    
    # Mark OTP as used
    otp_record.is_used = True
    
    await db.commit()
    await db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(new_user.id),
            "email": new_user.email,
            "email_verified": new_user.email_verified,
            "is_active": new_user.is_active,
        }
    )


@router.post("/login/send-otp", response_model=SendOTPResponse)
async def send_login_otp(
    request: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send OTP for user login
    """
    email = request.email.lower().strip()
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate OTP
    otp_code = create_otp_code()
    hashed_otp = hash_otp(otp_code)
    expires_at = get_otp_expiration()
    
    # Store OTP in database
    otp_record = OTP(
        email=email,
        otp_code=hashed_otp,
        purpose="login",
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    await db.commit()
    
    # Send OTP via email
    email_sent = await send_otp_email(email, otp_code, "login")
    
    if not email_sent:
        pass  # Log error but don't fail request
    
    return SendOTPResponse(
        message="OTP sent to your email address"
    )


@router.post("/login/verify-otp", response_model=TokenResponse)
async def verify_login_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and login user
    """
    email = request.email.lower().strip()
    otp_code = request.otp
    
    # Find valid OTP
    result = await db.execute(
        select(OTP).where(
            and_(
                OTP.email == email,
                OTP.purpose == "login",
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            )
        ).order_by(OTP.created_at.desc())
    )
    otp_record = result.scalar_one_or_none()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Verify OTP
    if not verify_otp(otp_code, otp_record.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Get user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Mark OTP as used
    otp_record.is_used = True
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": str(user.id),
            "email": user.email,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
        }
    )



