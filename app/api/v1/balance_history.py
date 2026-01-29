"""
Balance History API endpoints
"""

from datetime import date as date_type
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.balance_history import BalanceHistory
from app.models.expense import Expense
from app.models.income import Income
from app.models.user import User
from app.schemas.balance_history import BalanceHistoryResponse, RecalculateRequest

router = APIRouter()


async def update_balance_history_for_date(db: AsyncSession, user_id, target_date: date_type):
    """
    Calculate and update balance history for a specific date
    """
    from uuid import UUID

    # Convert user_id to UUID if it's a string
    if isinstance(user_id, str):
        user_uuid = UUID(user_id)
    else:
        user_uuid = user_id

    # Get total income for the date
    income_result = await db.execute(
        select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == user_uuid, Income.date == target_date)
    )
    total_income = int(income_result.scalar_one() or 0)

    # Get total expense for the date
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == user_uuid, Expense.date == target_date)
    )
    total_expense = int(expense_result.scalar_one() or 0)

    # Get most recent balance before target_date (could be previous day or earlier)
    previous_balance_result = await db.execute(
        select(BalanceHistory.balance)
        .where(BalanceHistory.user_id == user_uuid, BalanceHistory.date < target_date)
        .order_by(BalanceHistory.date.desc())
        .limit(1)
    )
    previous_balance_row = previous_balance_result.scalar_one_or_none()
    if previous_balance_row is not None:
        try:
            previous_balance = int(previous_balance_row)
        except (ValueError, TypeError):
            previous_balance = 0
    else:
        previous_balance = 0

    # Calculate new balance
    balance = previous_balance + total_income - total_expense

    # Update or create balance history record
    existing_result = await db.execute(
        select(BalanceHistory).where(BalanceHistory.user_id == user_uuid, BalanceHistory.date == target_date)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.total_income = total_income
        existing.total_expense = total_expense
        existing.balance = balance
    else:
        new_history = BalanceHistory(
            user_id=user_uuid,
            date=target_date,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
        )
        db.add(new_history)

    await db.flush()  # Flush instead of commit to allow transaction control
    return balance


async def recalculate_balance_from_date(db: AsyncSession, user_id, from_date: date_type):
    """
    Recalculate balance history from a specific date onwards.
    This is needed when an income/expense is created, updated, or deleted.
    
    IMPORTANT: We must recalculate ALL dates from from_date to today, not just
    dates with transactions, because balance is cumulative. Changing a transaction
    on day 5 affects the balance on days 5, 6, 7, 8... all the way to today.
    """
    today = date_type.today()
    
    from uuid import UUID
    
    if isinstance(user_id, str):
        user_uuid = UUID(user_id)
    else:
        user_uuid = user_id
    
    # Recalculate balance for EVERY date from from_date to today (inclusive)
    # This ensures cumulative balance is correct for all dates
    current_date = from_date
    while current_date <= today:
        await update_balance_history_for_date(db, user_uuid, current_date)
        current_date = current_date + timedelta(days=1)
    
    # Commit all balance history updates
    await db.commit()


@router.get("/", response_model=List[BalanceHistoryResponse])
async def get_balance_history(
    start_date: Optional[date_type] = Query(None, description="Filter from this date"),
    end_date: Optional[date_type] = Query(None, description="Filter until this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get balance history with optional date range filter
    """
    query = select(BalanceHistory).where(BalanceHistory.user_id == current_user.id)

    if start_date:
        query = query.where(BalanceHistory.date >= start_date)

    if end_date:
        query = query.where(BalanceHistory.date <= end_date)

    result = await db.execute(query.order_by(BalanceHistory.date.desc()))
    history = result.scalars().all()

    return history


@router.post("/recalculate", status_code=status.HTTP_200_OK)
async def recalculate_balance_history(
    recalc_data: RecalculateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Recalculate balance history from a specific date
    """
    # Determine start date
    if recalc_data.from_date:
        start_date = recalc_data.from_date
    else:
        # Get earliest income or expense date
        earliest_income_result = await db.execute(select(func.min(Income.date)).where(Income.user_id == current_user.id))
        earliest_income = earliest_income_result.scalar_one()

        earliest_expense_result = await db.execute(select(func.min(Expense.date)).where(Expense.user_id == current_user.id))
        earliest_expense = earliest_expense_result.scalar_one()

        if earliest_income and earliest_expense:
            start_date = min(earliest_income, earliest_expense)
        elif earliest_income:
            start_date = earliest_income
        elif earliest_expense:
            start_date = earliest_expense
        else:
            return {"message": "No income or expense data found"}

    # Get all dates from start_date to today that have income or expenses
    income_dates_result = await db.execute(
        select(func.distinct(Income.date)).where(Income.user_id == current_user.id, Income.date >= start_date)
    )
    income_dates = set(row[0] for row in income_dates_result.all() if row[0])

    expense_dates_result = await db.execute(
        select(func.distinct(Expense.date)).where(Expense.user_id == current_user.id, Expense.date >= start_date)
    )
    expense_dates = set(row[0] for row in expense_dates_result.all() if row[0])

    dates = sorted(list(income_dates | expense_dates))

    # Also include today if not in the list
    today = date_type.today()
    if today not in dates:
        dates.append(today)

    dates.sort()

    # Recalculate balance for each date
    recalculated_count = 0
    for date in dates:
        await update_balance_history_for_date(db, current_user.id, date)
        recalculated_count += 1

    return {
        "message": f"Recalculated balance history for {recalculated_count} date(s)",
        "from_date": start_date.isoformat(),
        "dates_recalculated": recalculated_count,
    }
