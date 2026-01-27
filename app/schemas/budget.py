"""
Pydantic schemas for Budget API
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator


class BudgetBase(BaseModel):
    """Base budget schema"""

    name: str = Field(..., min_length=1, max_length=255, description="Budget name")
    amount: int = Field(..., gt=0, description="Budget amount in cents/smallest unit")
    icon: Optional[str] = Field(None, max_length=50, description="Budget icon identifier")


class BudgetCreate(BudgetBase):
    """Schema for creating a budget"""

    pass


class BudgetUpdate(BaseModel):
    """Schema for updating a budget"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[int] = Field(None, gt=0)
    icon: Optional[str] = Field(None, max_length=50)


class BudgetResponse(BudgetBase):
    """Schema for budget response"""

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

    @field_serializer("user_id")
    def serialize_user_id(self, value: UUID | str, _info) -> str:
        """Convert UUID to string if needed during serialization"""
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True


class BudgetSummary(BudgetResponse):
    """Budget with summary statistics"""

    total_spent: int = Field(0, description="Total spent in cents")
    remaining: int = Field(0, description="Remaining amount in cents")
    expenses_count: int = Field(0, description="Number of expenses")

    class Config:
        from_attributes = True
