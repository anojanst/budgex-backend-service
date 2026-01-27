"""
Pydantic schemas for Balance History API
"""

from datetime import date as date_type
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BalanceHistoryResponse(BaseModel):
    """Schema for balance history response"""

    id: int
    user_id: str
    date: date_type
    total_income: int
    total_expense: int
    balance: int
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


class RecalculateRequest(BaseModel):
    """Schema for recalculating balance history"""

    from_date: Optional[date_type] = Field(None, description="Recalculate from this date (defaults to earliest date)")
