"""
Loan API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import date as date_type, datetime, timedelta

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.loan import Loan, LoanRepayment
from app.schemas.loan import (
    LoanCreate, LoanUpdate, LoanResponse, LoanWithRepayments,
    LoanRepaymentResponse, LoanRepaymentCreate
)

router = APIRouter()


@router.get("/", response_model=List[LoanResponse])
async def list_loans(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all loans for the current user
    """
    result = await db.execute(
        select(Loan).where(Loan.user_id == current_user.id).order_by(Loan.created_at.desc())
    )
    loans = result.scalars().all()
    return loans


@router.get("/{loan_id}", response_model=LoanWithRepayments)
async def get_loan(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get loan details with repayment schedule
    """
    result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.user_id == current_user.id
        )
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Get repayments
    repayments_result = await db.execute(
        select(LoanRepayment).where(LoanRepayment.loan_id == loan_id)
        .order_by(LoanRepayment.payment_date.desc())
    )
    repayments = repayments_result.scalars().all()
    
    # Calculate totals
    total_paid_result = await db.execute(
        select(func.coalesce(func.sum(LoanRepayment.amount), 0))
        .where(LoanRepayment.loan_id == loan_id)
    )
    total_paid = int(total_paid_result.scalar_one() or 0)
    
    return {
        **loan.__dict__,
        "repayments": repayments,
        "total_paid": total_paid,
    }


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(
    loan_data: LoanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new loan
    """
    new_loan = Loan(
        user_id=current_user.id,
        lender=loan_data.lender,
        principal_amount=loan_data.principal_amount,
        remaining_principal=loan_data.remaining_principal,
        interest_rate=loan_data.interest_rate,
        tenure_months=loan_data.tenure_months,
        repayment_frequency=loan_data.repayment_frequency,
        emi=loan_data.emi,
        next_due_date=loan_data.next_due_date,
        is_paid_off=loan_data.is_paid_off,
    )
    
    db.add(new_loan)
    await db.commit()
    await db.refresh(new_loan)
    
    return new_loan


@router.patch("/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: int,
    loan_data: LoanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a loan
    """
    result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.user_id == current_user.id
        )
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Update fields
    if loan_data.lender is not None:
        loan.lender = loan_data.lender
    if loan_data.principal_amount is not None:
        loan.principal_amount = loan_data.principal_amount
    if loan_data.remaining_principal is not None:
        loan.remaining_principal = loan_data.remaining_principal
    if loan_data.interest_rate is not None:
        loan.interest_rate = loan_data.interest_rate
    if loan_data.tenure_months is not None:
        loan.tenure_months = loan_data.tenure_months
    if loan_data.repayment_frequency is not None:
        loan.repayment_frequency = loan_data.repayment_frequency
    if loan_data.emi is not None:
        loan.emi = loan_data.emi
    if loan_data.next_due_date is not None:
        loan.next_due_date = loan_data.next_due_date
    if loan_data.is_paid_off is not None:
        loan.is_paid_off = loan_data.is_paid_off
    
    await db.commit()
    await db.refresh(loan)
    
    return loan


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a loan (cascades to repayments)
    """
    result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.user_id == current_user.id
        )
    )
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    await db.delete(loan)
    await db.commit()
    
    return None


@router.post("/{loan_id}/repayments/", response_model=LoanRepaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_repayment(
    loan_id: int,
    repayment_data: LoanRepaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a loan repayment record
    """
    # Verify loan belongs to user
    loan_result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.user_id == current_user.id
        )
    )
    loan = loan_result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Validate expense_id if provided
    if repayment_data.expense_id:
        from app.models.expense import Expense
        expense_result = await db.execute(
            select(Expense).where(
                Expense.id == repayment_data.expense_id,
                Expense.user_id == current_user.id
            )
        )
        if not expense_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
    
    new_repayment = LoanRepayment(
        loan_id=loan_id,
        user_id=current_user.id,
        scheduled_date=repayment_data.scheduled_date,
        amount=repayment_data.amount,
        principal_amount=repayment_data.principal_amount,
        interest_amount=repayment_data.interest_amount,
        status=repayment_data.status,
        expense_id=repayment_data.expense_id,
    )
    
    db.add(new_repayment)
    
    # Update loan remaining principal if payment is made
    if repayment_data.status == "paid":
        loan.remaining_principal = max(0, loan.remaining_principal - repayment_data.principal_amount)
        if loan.remaining_principal == 0:
            loan.is_paid_off = True
    
    await db.commit()
    await db.refresh(new_repayment)
    
    return new_repayment


@router.get("/{loan_id}/repayments/", response_model=List[LoanRepaymentResponse])
async def get_repayments(
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get repayment schedule for a loan
    """
    # Verify loan belongs to user
    loan_result = await db.execute(
        select(Loan).where(
            Loan.id == loan_id,
            Loan.user_id == current_user.id
        )
    )
    if not loan_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    result = await db.execute(
        select(LoanRepayment).where(LoanRepayment.loan_id == loan_id)
        .order_by(LoanRepayment.scheduled_date.desc())
    )
    repayments = result.scalars().all()
    
    return repayments

