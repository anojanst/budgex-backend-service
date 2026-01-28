"""
Loan API endpoints
"""

from datetime import date, date as date_type
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.loan import Loan, LoanRepayment
from app.models.user import User
from app.schemas.loan import (
    LoanCreate,
    LoanRepaymentCreate,
    LoanRepaymentResponse,
    LoanResponse,
    LoanUpdate,
    LoanWithRepayments,
    MarkRepaymentPaid,
)

router = APIRouter()


def generate_repayment_schedule(
    loan_id: int,
    user_id: UUID,
    principal_amount: int,
    interest_rate: Decimal,
    tenure_months: int,
    repayment_frequency: str,
    emi: int,
    start_date: date_type,
) -> List[LoanRepayment]:
    """
    Generate repayment schedule for a loan
    
    Args:
        loan_id: Loan ID
        user_id: User ID
        principal_amount: Initial principal amount in cents
        interest_rate: Annual interest rate as Decimal (e.g., 5.5 for 5.5%)
        tenure_months: Loan tenure in months
        repayment_frequency: 'monthly' or 'weekly'
        emi: EMI amount in cents
        start_date: First payment date
    
    Returns:
        List of LoanRepayment objects
    """
    repayments = []
    remaining_principal = principal_amount
    current_date = start_date
    
    # Calculate number of payments and date increment
    if repayment_frequency.lower() == "monthly":
        num_payments = tenure_months
        date_increment = lambda d: d + relativedelta(months=1)
    elif repayment_frequency.lower() == "weekly":
        num_payments = tenure_months * 4  # Approximate: 4 weeks per month
        date_increment = lambda d: d + timedelta(weeks=1)
    else:
        # Default to monthly if frequency is not recognized
        num_payments = tenure_months
        date_increment = lambda d: d + relativedelta(months=1)
    
    # Monthly interest rate (annual rate / 12)
    monthly_rate = float(interest_rate) / 100 / 12
    
    for payment_num in range(1, num_payments + 1):
        # Calculate interest for this payment
        # For monthly: interest = remaining_principal * monthly_rate
        # For weekly: interest = remaining_principal * (annual_rate / 100 / 52)
        if repayment_frequency.lower() == "weekly":
            period_rate = float(interest_rate) / 100 / 52
        else:
            period_rate = monthly_rate
        
        interest_amount = int(remaining_principal * period_rate)
        
        # Principal amount is EMI minus interest
        principal_amount_payment = emi - interest_amount
        
        # For the last payment, adjust to ensure remaining principal is fully paid
        if payment_num == num_payments:
            principal_amount_payment = remaining_principal
            emi_adjusted = principal_amount_payment + interest_amount
        else:
            emi_adjusted = emi
        
        # Ensure principal doesn't go negative
        if principal_amount_payment > remaining_principal:
            principal_amount_payment = remaining_principal
            emi_adjusted = principal_amount_payment + interest_amount
        
        # Create repayment record
        repayment = LoanRepayment(
            loan_id=loan_id,
            user_id=user_id,
            scheduled_date=current_date,
            amount=emi_adjusted,
            principal_amount=principal_amount_payment,
            interest_amount=interest_amount,
            status="pending",
            expense_id=None,
        )
        
        repayments.append(repayment)
        
        # Update remaining principal
        remaining_principal -= principal_amount_payment
        
        # Break if principal is fully paid
        if remaining_principal <= 0:
            break
        
        # Move to next payment date
        current_date = date_increment(current_date)
    
    return repayments


@router.get("/", response_model=List[LoanResponse])
async def list_loans(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all loans for the current user
    """
    result = await db.execute(select(Loan).where(Loan.user_id == current_user.id).order_by(Loan.created_at.desc()))
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
    result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id))
    loan = result.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    # Get repayments
    repayments_result = await db.execute(
        select(LoanRepayment).where(LoanRepayment.loan_id == loan_id).order_by(LoanRepayment.scheduled_date.desc())
    )
    repayments = repayments_result.scalars().all()

    # Calculate totals
    total_paid_result = await db.execute(
        select(func.coalesce(func.sum(LoanRepayment.amount), 0)).where(LoanRepayment.loan_id == loan_id)
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
    Create a new loan and automatically generate repayment schedule
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
    await db.flush()  # Flush to get the loan ID without committing

    # Generate repayment schedule
    repayments = generate_repayment_schedule(
        loan_id=new_loan.id,
        user_id=current_user.id,  # UUID type
        principal_amount=loan_data.remaining_principal,  # Use remaining_principal as starting point
        interest_rate=loan_data.interest_rate,
        tenure_months=loan_data.tenure_months,
        repayment_frequency=loan_data.repayment_frequency,
        emi=loan_data.emi,
        start_date=loan_data.next_due_date,
    )

    # Add all repayments to the session
    for repayment in repayments:
        db.add(repayment)

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
    result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id))
    loan = result.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

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
    result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id))
    loan = result.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    await db.delete(loan)
    await db.commit()

    return None


@router.post(
    "/{loan_id}/repayments/",
    response_model=LoanRepaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    loan_result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id))
    loan = loan_result.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    # Validate expense_id if provided
    if repayment_data.expense_id:
        from app.models.expense import Expense

        expense_result = await db.execute(
            select(Expense).where(
                Expense.id == repayment_data.expense_id,
                Expense.user_id == current_user.id,
            )
        )
        if not expense_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Convert 0 to None for optional foreign keys
    expense_id = repayment_data.expense_id if repayment_data.expense_id else None

    new_repayment = LoanRepayment(
        loan_id=loan_id,
        user_id=current_user.id,
        scheduled_date=repayment_data.scheduled_date,
        amount=repayment_data.amount,
        principal_amount=repayment_data.principal_amount,
        interest_amount=repayment_data.interest_amount,
        status=repayment_data.status,
        expense_id=expense_id,
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
    loan_result = await db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == current_user.id))
    if not loan_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    result = await db.execute(
        select(LoanRepayment).where(LoanRepayment.loan_id == loan_id).order_by(LoanRepayment.scheduled_date.desc())
    )
    repayments = result.scalars().all()

    return repayments


@router.patch(
    "/repayments/{repayment_id}/mark-paid",
    response_model=LoanRepaymentResponse,
)
async def mark_repayment_paid(
    repayment_id: int,
    payment_data: MarkRepaymentPaid,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a repayment as paid and create an associated expense
    """
    from app.models.expense import Expense
    from app.models.budget import Budget
    from app.models.tag import Tag

    # Get repayment with loan
    repayment_result = await db.execute(
        select(LoanRepayment)
        .join(Loan)
        .where(
            LoanRepayment.id == repayment_id,
            Loan.user_id == current_user.id,
        )
    )
    repayment = repayment_result.scalar_one_or_none()

    if not repayment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repayment not found")

    # Check if already paid
    if repayment.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repayment is already marked as paid",
        )

    # Get the loan
    loan_result = await db.execute(select(Loan).where(Loan.id == repayment.loan_id))
    loan = loan_result.scalar_one_or_none()

    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")

    # Validate budget_id if provided
    budget_id = payment_data.budget_id if payment_data.budget_id else None
    if budget_id:
        budget_result = await db.execute(
            select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
        )
        if not budget_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Validate tag_id if provided
    tag_id = payment_data.tag_id if payment_data.tag_id else None
    if tag_id:
        tag_result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
        if not tag_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Create expense for the payment
    payment_date = payment_data.payment_date if payment_data.payment_date else date.today()
    expense_name = payment_data.expense_name if payment_data.expense_name else f"Loan Payment - {loan.lender}"

    new_expense = Expense(
        user_id=current_user.id,
        name=expense_name,
        amount=repayment.amount,
        date=payment_date,
        budget_id=budget_id,
        tag_id=tag_id,
    )

    db.add(new_expense)
    await db.flush()  # Flush to get expense ID

    # Update repayment status and link expense
    repayment.status = "paid"
    repayment.expense_id = new_expense.id

    # Update loan remaining principal
    loan.remaining_principal = max(0, loan.remaining_principal - repayment.principal_amount)

    # Check if loan is fully paid off
    if loan.remaining_principal == 0:
        loan.is_paid_off = True

    # Update next_due_date to the next pending repayment
    next_repayment_result = await db.execute(
        select(LoanRepayment)
        .where(
            LoanRepayment.loan_id == loan.id,
            LoanRepayment.status == "pending",
        )
        .order_by(LoanRepayment.scheduled_date.asc())
        .limit(1)
    )
    next_repayment = next_repayment_result.scalar_one_or_none()
    if next_repayment:
        loan.next_due_date = next_repayment.scheduled_date

    await db.commit()
    await db.refresh(repayment)

    return repayment
