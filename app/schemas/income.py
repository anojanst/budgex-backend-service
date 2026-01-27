"""
Pydantic schemas for Income API
"""

from datetime import date as date_type
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.income import IncomeCategory


class IncomeBase(BaseModel):
    """Base income schema"""

    name: str = Field(..., min_length=1, max_length=255, description="Income name")
    amount: int = Field(..., gt=0, description="Income amount in cents/smallest unit")
    category: IncomeCategory = Field(..., description="Income category")
    date: date_type = Field(..., description="Income date")
    tag_id: Optional[int] = Field(None, description="Global tag ID (optional)")

    @field_validator("tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class IncomeCreate(IncomeBase):
    """Schema for creating an income"""

    pass


class IncomeUpdate(BaseModel):
    """Schema for updating an income"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[int] = Field(None, gt=0)
    category: Optional[IncomeCategory] = None
    date: Optional[date_type] = None
    tag_id: Optional[int] = None

    @field_validator("tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class IncomeResponse(IncomeBase):
    """Schema for income response"""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def convert_user_id(cls, value: UUID | str) -> str:
        """Convert UUID to string if needed"""
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True


class IncomeWithTag(IncomeResponse):
    """Income with tag info"""

    tag_name: Optional[str] = None
    tag_color: Optional[str] = None

    class Config:
        from_attributes = True
