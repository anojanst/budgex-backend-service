"""
Expense API endpoints
"""

from datetime import date as date_type
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.tag import Tag
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    ExpenseWithRelations,
)

router = APIRouter()


@router.get("/", response_model=List[ExpenseWithRelations])
async def list_expenses(
    budget_id: Optional[int] = Query(None, description="Filter by budget ID"),
    tag_id: Optional[int] = Query(None, description="Filter by tag ID"),
    start_date: Optional[date_type] = Query(None, description="Filter expenses from this date"),
    end_date: Optional[date_type] = Query(None, description="Filter expenses until this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List expenses with optional filters

    - **budget_id**: Filter by budget
    - **tag_id**: Filter by tag
    - **start_date**: Filter expenses from this date
    - **end_date**: Filter expenses until this date
    """
    query = select(Expense).where(Expense.user_id == current_user.id)

    if budget_id:
        query = query.where(Expense.budget_id == budget_id)

    if tag_id:
        query = query.where(Expense.tag_id == tag_id)

    if start_date:
        query = query.where(Expense.date >= start_date)

    if end_date:
        query = query.where(Expense.date <= end_date)

    result = await db.execute(query.order_by(Expense.date.desc(), Expense.created_at.desc()))
    expenses = result.scalars().all()

    # Load related budget and tag info
    expenses_with_relations = []
    for expense in expenses:
        expense_dict = {
            **expense.__dict__,
            "budget_name": None,
            "tag_name": None,
            "tag_color": None,
        }

        if expense.budget_id:
            budget_result = await db.execute(select(Budget).where(Budget.id == expense.budget_id))
            budget = budget_result.scalar_one_or_none()
            if budget:
                expense_dict["budget_name"] = budget.name

        if expense.tag_id:
            tag_result = await db.execute(select(Tag).where(Tag.id == expense.tag_id))
            tag = tag_result.scalar_one_or_none()
            if tag:
                expense_dict["tag_name"] = tag.name
                expense_dict["tag_color"] = tag.color

        expenses_with_relations.append(expense_dict)

    return expenses_with_relations


@router.get("/{expense_id}", response_model=ExpenseWithRelations)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get expense details
    """
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id))
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    expense_dict = {
        **expense.__dict__,
        "budget_name": None,
        "tag_name": None,
        "tag_color": None,
    }

    if expense.budget_id:
        budget_result = await db.execute(select(Budget).where(Budget.id == expense.budget_id))
        budget = budget_result.scalar_one_or_none()
        if budget:
            expense_dict["budget_name"] = budget.name

    if expense.tag_id:
        tag_result = await db.execute(select(Tag).where(Tag.id == expense.tag_id))
        tag = tag_result.scalar_one_or_none()
        if tag:
            expense_dict["tag_name"] = tag.name
            expense_dict["tag_color"] = tag.color

    return expense_dict


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new expense (tag_id can be any global tag)
    """
    # Validate budget_id if provided
    if expense_data.budget_id:
        budget_result = await db.execute(
            select(Budget).where(Budget.id == expense_data.budget_id, Budget.user_id == current_user.id)
        )
        if not budget_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Validate tag_id if provided
    if expense_data.tag_id:
        tag_result = await db.execute(select(Tag).where(Tag.id == expense_data.tag_id, Tag.user_id == current_user.id))
        if not tag_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Convert 0 to None for optional foreign keys (validator should handle this, but being explicit)
    budget_id = expense_data.budget_id if expense_data.budget_id else None
    tag_id = expense_data.tag_id if expense_data.tag_id else None

    new_expense = Expense(
        user_id=current_user.id,
        name=expense_data.name,
        amount=expense_data.amount,
        date=expense_data.date,
        budget_id=budget_id,
        tag_id=tag_id,
    )

    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    # Recalculate balance history from expense date onwards
    try:
        from app.api.v1.balance_history import recalculate_balance_from_date
        await recalculate_balance_from_date(db, current_user.id, expense_data.date)
    except Exception as e:
        # Log error but don't fail the request
        # Balance can be recalculated manually if needed
        import logging
        logging.error(f"Failed to recalculate balance history: {e}")

    return new_expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an expense (including tag_id)
    """
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id))
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Validate budget_id if provided
    if expense_data.budget_id is not None:
        if expense_data.budget_id:
            budget_result = await db.execute(
                select(Budget).where(
                    Budget.id == expense_data.budget_id,
                    Budget.user_id == current_user.id,
                )
            )
            if not budget_result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Validate tag_id if provided
    if expense_data.tag_id is not None:
        if expense_data.tag_id:
            tag_result = await db.execute(select(Tag).where(Tag.id == expense_data.tag_id, Tag.user_id == current_user.id))
            if not tag_result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Store old date before update
    old_date = expense.date
    dates_to_recalculate = {old_date}

    # Update fields
    if expense_data.name is not None:
        expense.name = expense_data.name
    if expense_data.amount is not None:
        expense.amount = expense_data.amount
    if expense_data.date is not None:
        expense.date = expense_data.date
        dates_to_recalculate.add(expense_data.date)  # Add new date if changed
    if expense_data.budget_id is not None:
        expense.budget_id = expense_data.budget_id if expense_data.budget_id else None
    if expense_data.tag_id is not None:
        expense.tag_id = expense_data.tag_id if expense_data.tag_id else None

    await db.commit()
    await db.refresh(expense)

    # Recalculate balance history from the earliest affected date onwards
    try:
        from app.api.v1.balance_history import recalculate_balance_from_date
        earliest_date = min(dates_to_recalculate)
        await recalculate_balance_from_date(db, current_user.id, earliest_date)
    except Exception as e:
        import logging
        logging.error(f"Failed to recalculate balance history: {e}")

    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an expense
    """
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id))
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Store date before deletion for recalculation
    expense_date = expense.date

    await db.delete(expense)
    await db.commit()

    # Recalculate balance history from expense date onwards
    try:
        from app.api.v1.balance_history import recalculate_balance_from_date
        await recalculate_balance_from_date(db, current_user.id, expense_date)
    except Exception as e:
        import logging
        logging.error(f"Failed to recalculate balance history: {e}")

    return None


@router.get("/budgets/{budget_id}/expenses/", response_model=List[ExpenseWithRelations])
async def get_budget_expenses(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all expenses for a specific budget
    """
    # Verify budget belongs to user
    budget_result = await db.execute(select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id))
    if not budget_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Get expenses
    result = await db.execute(
        select(Expense)
        .where(Expense.budget_id == budget_id, Expense.user_id == current_user.id)
        .order_by(Expense.date.desc(), Expense.created_at.desc())
    )
    expenses = result.scalars().all()

    # Load related tag info
    expenses_with_relations = []
    for expense in expenses:
        expense_dict = {
            **expense.__dict__,
            "budget_name": None,
            "tag_name": None,
            "tag_color": None,
        }

        expense_dict["budget_name"] = None  # We know it's this budget

        if expense.tag_id:
            tag_result = await db.execute(select(Tag).where(Tag.id == expense.tag_id))
            tag = tag_result.scalar_one_or_none()
            if tag:
                expense_dict["tag_name"] = tag.name
                expense_dict["tag_color"] = tag.color

        expenses_with_relations.append(expense_dict)

    return expenses_with_relations
