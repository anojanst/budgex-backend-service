"""
Pydantic schemas for Saving Goal API
"""

from datetime import date as date_type
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SavingContributionBase(BaseModel):
    """Base saving contribution schema"""

    amount: int = Field(..., gt=0, description="Contribution amount in cents")
    date: date_type = Field(..., description="Contribution date")
    expense_id: Optional[int] = Field(None, description="Linked expense ID if applicable")

    @field_validator("expense_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class SavingContributionCreate(SavingContributionBase):
    """Schema for creating a saving contribution"""

    pass


class SavingContributionResponse(SavingContributionBase):
    """Schema for saving contribution response"""

    id: int
    goal_id: int
    user_id: str
    created_at: date_type

    @field_validator("user_id", mode="before")
    @classmethod
    def convert_user_id(cls, value: UUID | str) -> str:
        """Convert UUID to string if needed"""
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True


class SavingGoalBase(BaseModel):
    """Base saving goal schema"""

    title: str = Field(..., min_length=1, max_length=255, description="Goal title")
    target_amount: int = Field(..., gt=0, description="Target amount in cents")
    target_date: date_type = Field(..., description="Target date")


class SavingGoalCreate(SavingGoalBase):
    """Schema for creating a saving goal"""

    pass


class SavingGoalUpdate(BaseModel):
    """Schema for updating a saving goal"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[int] = Field(None, gt=0)
    target_date: Optional[date_type] = None


class SavingGoalResponse(SavingGoalBase):
    """Schema for saving goal response"""

    id: int
    user_id: str
    created_at: date_type
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


class SavingGoalWithContributions(SavingGoalResponse):
    """Saving goal with contributions and progress"""

    contributions: List[SavingContributionResponse] = Field(default_factory=list)
    total_contributed: int = Field(0, description="Total contributed in cents")
    remaining_amount: int = Field(0, description="Remaining amount in cents")
    progress_percentage: float = Field(0, ge=0, le=100, description="Progress percentage")

    class Config:
        from_attributes = True
