"""
User management endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User

router = APIRouter()


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: str
    email: str
    email_verified: bool
    is_active: bool
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        created_at=(current_user.created_at.isoformat() if current_user.created_at else None),
        last_login_at=(current_user.last_login_at.isoformat() if current_user.last_login_at else None),
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user information
    Note: Email changes would require re-verification (not implemented yet)
    """
    if user_update.email and user_update.email != current_user.email:
        # Check if new email is already taken
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.email == user_update.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

        # Update email and mark as unverified (requires re-verification)
        current_user.email = user_update.email.lower().strip()
        current_user.email_verified = False

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        created_at=(current_user.created_at.isoformat() if current_user.created_at else None),
        last_login_at=(current_user.last_login_at.isoformat() if current_user.last_login_at else None),
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete current user account (soft delete by deactivating)
    """
    current_user.is_active = False
    await db.commit()

    return None
