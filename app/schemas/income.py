"""
Pydantic schemas for Income API
"""

from datetime import date as date_type
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.income import IncomeCategory


class IncomeBase(BaseModel):
    """Base income schema"""

    name: str = Field(..., min_length=1, max_length=255, description="Income name")
    amount: int = Field(..., gt=0, description="Income amount in cents/smallest unit")
    category: IncomeCategory = Field(..., description="Income category")
    date: date_type = Field(..., description="Income date")
    tag_id: Optional[int] = Field(None, description="Global tag ID (optional)")


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


class IncomeResponse(IncomeBase):
    """Schema for income response"""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncomeWithTag(IncomeResponse):
    """Income with tag info"""

    tag_name: Optional[str] = None
    tag_color: Optional[str] = None

    class Config:
        from_attributes = True
