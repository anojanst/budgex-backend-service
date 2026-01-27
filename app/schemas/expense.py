"""
Pydantic schemas for Expense API
"""

from datetime import date as date_type
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ExpenseBase(BaseModel):
    """Base expense schema"""

    name: str = Field(..., min_length=1, max_length=255, description="Expense name")
    amount: int = Field(..., gt=0, description="Expense amount in cents/smallest unit")
    date: date_type = Field(..., description="Expense date")
    budget_id: Optional[int] = Field(None, description="Budget ID (optional)")
    tag_id: Optional[int] = Field(None, description="Global tag ID (optional)")

    @field_validator("budget_id", "tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class ExpenseCreate(ExpenseBase):
    """Schema for creating an expense"""

    pass


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[int] = Field(None, gt=0)
    date: Optional[date_type] = None
    budget_id: Optional[int] = None
    tag_id: Optional[int] = None

    @field_validator("budget_id", "tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class ExpenseResponse(ExpenseBase):
    """Schema for expense response"""

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


class ExpenseWithRelations(ExpenseResponse):
    """Expense with related budget and tag info"""

    budget_name: Optional[str] = None
    tag_name: Optional[str] = None
    tag_color: Optional[str] = None

    class Config:
        from_attributes = True
