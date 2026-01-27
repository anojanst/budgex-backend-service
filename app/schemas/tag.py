"""
Pydantic schemas for Tag API
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema"""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    color: Optional[str] = Field(None, max_length=7, description="Tag color (hex code)")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")


class TagCreate(TagBase):
    """Schema for creating a tag"""

    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, max_length=7)
    description: Optional[str] = Field(None, max_length=500)


class TagResponse(TagBase):
    """Schema for tag response"""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagWithStats(TagResponse):
    """Tag with usage statistics"""

    expenses_count: int = Field(0, description="Number of expenses with this tag")
    incomes_count: int = Field(0, description="Number of incomes with this tag")
    total_spent: int = Field(0, description="Total spent from expenses in cents")
    total_earned: int = Field(0, description="Total earned from incomes in cents")
    budgets_used_in: List[int] = Field(default_factory=list, description="Budget IDs where tag is used")

    class Config:
        from_attributes = True
