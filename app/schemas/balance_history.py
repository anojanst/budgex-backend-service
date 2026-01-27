"""
Pydantic schemas for Balance History API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date as date_type, datetime


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
    
    class Config:
        from_attributes = True


class RecalculateRequest(BaseModel):
    """Schema for recalculating balance history"""
    from_date: Optional[date_type] = Field(None, description="Recalculate from this date (defaults to earliest date)")

