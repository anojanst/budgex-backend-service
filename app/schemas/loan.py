"""
Pydantic schemas for Loan API
"""

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LoanBase(BaseModel):
    """Base loan schema"""

    lender: str = Field(..., min_length=1, max_length=255, description="Lender name")
    principal_amount: int = Field(..., gt=0, description="Principal amount in cents")
    remaining_principal: int = Field(..., ge=0, description="Remaining principal in cents")
    interest_rate: Decimal = Field(..., ge=0, le=100, description="Annual interest rate percentage")
    tenure_months: int = Field(..., gt=0, description="Loan tenure in months")
    repayment_frequency: str = Field(..., description="Repayment frequency (e.g., 'monthly', 'weekly')")
    emi: int = Field(..., gt=0, description="EMI amount in cents")
    next_due_date: date_type = Field(..., description="Next due date")
    is_paid_off: bool = Field(default=False, description="Whether loan is paid off")


class LoanCreate(LoanBase):
    """Schema for creating a loan"""

    pass


class LoanUpdate(BaseModel):
    """Schema for updating a loan"""

    lender: Optional[str] = Field(None, min_length=1, max_length=255)
    principal_amount: Optional[int] = Field(None, gt=0)
    remaining_principal: Optional[int] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tenure_months: Optional[int] = Field(None, gt=0)
    repayment_frequency: Optional[str] = None
    emi: Optional[int] = Field(None, gt=0)
    next_due_date: Optional[date_type] = None
    is_paid_off: Optional[bool] = None


class LoanRepaymentResponse(BaseModel):
    """Schema for loan repayment response"""

    id: int
    loan_id: int
    user_id: str
    scheduled_date: date_type
    amount: int
    principal_amount: int
    interest_amount: int
    status: str
    expense_id: Optional[int] = None
    created_at: datetime

    @field_validator("user_id", mode="before")
    @classmethod
    def convert_user_id(cls, value: UUID | str) -> str:
        """Convert UUID to string if needed"""
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True


class LoanResponse(LoanBase):
    """Schema for loan response"""

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


class LoanWithRepayments(LoanResponse):
    """Loan with repayment schedule"""

    repayments: List[LoanRepaymentResponse] = Field(default_factory=list)
    total_paid: int = Field(0, description="Total amount paid in cents")

    class Config:
        from_attributes = True


class LoanRepaymentCreate(BaseModel):
    """Schema for creating a loan repayment"""

    scheduled_date: date_type = Field(..., description="Scheduled payment date")
    amount: int = Field(..., gt=0, description="Payment amount in cents")
    principal_amount: int = Field(..., ge=0, description="Principal portion in cents")
    interest_amount: int = Field(..., ge=0, description="Interest portion in cents")
    status: str = Field(default="paid", description="Payment status: 'pending', 'paid', 'overdue'")
    expense_id: Optional[int] = Field(None, description="Linked expense ID if applicable")

    @field_validator("expense_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class MarkRepaymentPaid(BaseModel):
    """Schema for marking a repayment as paid"""

    payment_date: Optional[date_type] = Field(None, description="Actual payment date (defaults to today)")
    expense_name: Optional[str] = Field(None, max_length=255, description="Expense name (defaults to loan payment)")
    budget_id: Optional[int] = Field(None, description="Budget ID to link expense to")
    tag_id: Optional[int] = Field(None, description="Tag ID to link expense to")

    @field_validator("budget_id", "tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class AdditionalPayment(BaseModel):
    """Schema for making an additional payment on a loan"""

    amount: int = Field(..., gt=0, description="Additional payment amount in cents")
    payment_date: Optional[date_type] = Field(None, description="Payment date (defaults to today)")
    expense_name: Optional[str] = Field(
        None, max_length=255, description="Expense name (defaults to 'Additional Loan Payment - {lender}')"
    )
    budget_id: Optional[int] = Field(None, description="Budget ID to link expense to")
    tag_id: Optional[int] = Field(None, description="Tag ID to link expense to")

    @field_validator("budget_id", "tag_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, value: Optional[int]) -> Optional[int]:
        """Convert 0 to None for optional foreign keys"""
        if value == 0:
            return None
        return value


class PaymentDueSummary(BaseModel):
    """Schema for payment due summary"""

    count: int = Field(..., ge=0, description="Number of unpaid repayments due as of today")
    total_amount: int = Field(..., ge=0, description="Total amount of unpaid repayments due as of today in cents")
