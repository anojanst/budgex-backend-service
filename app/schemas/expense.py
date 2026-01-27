"""
Pydantic schemas for Expense API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date as date_type, datetime


class ExpenseBase(BaseModel):
    """Base expense schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Expense name")
    amount: int = Field(..., gt=0, description="Expense amount in cents/smallest unit")
    date: date_type = Field(..., description="Expense date")
    budget_id: Optional[int] = Field(None, description="Budget ID (optional)")
    tag_id: Optional[int] = Field(None, description="Global tag ID (optional)")


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


class ExpenseResponse(ExpenseBase):
    """Schema for expense response"""
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExpenseWithRelations(ExpenseResponse):
    """Expense with related budget and tag info"""
    budget_name: Optional[str] = None
    tag_name: Optional[str] = None
    tag_color: Optional[str] = None
    
    class Config:
        from_attributes = True

