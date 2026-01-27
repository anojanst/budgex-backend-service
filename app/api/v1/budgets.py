"""
Budget API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.budget import Budget
from app.models.expense import Expense
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSummary

router = APIRouter()


@router.get("/", response_model=List[BudgetSummary])
async def list_budgets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all budgets for the current user with summary statistics
    """
    # Get all budgets for user
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.created_at.desc())
    )
    budgets = result.scalars().all()
    
    # Calculate summary for each budget
    budgets_with_summary = []
    for budget in budgets:
        # Get total spent from expenses
        expense_result = await db.execute(
            select(
                func.coalesce(func.sum(Expense.amount), 0).label("total_spent"),
                func.count(Expense.id).label("expenses_count")
            ).where(Expense.budget_id == budget.id)
        )
        expense_stats = expense_result.first()
        
        total_spent = int(expense_stats.total_spent) if expense_stats.total_spent else 0
        expenses_count = expense_stats.expenses_count or 0
        remaining = budget.amount - total_spent
        
        budgets_with_summary.append({
            **budget.__dict__,
            "total_spent": total_spent,
            "remaining": remaining,
            "expenses_count": expenses_count,
        })
    
    return budgets_with_summary


@router.get("/{budget_id}", response_model=BudgetSummary)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get budget details with summary statistics
    """
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Calculate summary statistics
    expense_result = await db.execute(
        select(
            func.coalesce(func.sum(Expense.amount), 0).label("total_spent"),
            func.count(Expense.id).label("expenses_count")
        ).where(Expense.budget_id == budget.id)
    )
    expense_stats = expense_result.first()
    
    total_spent = int(expense_stats.total_spent) if expense_stats.total_spent else 0
    expenses_count = expense_stats.expenses_count or 0
    remaining = budget.amount - total_spent
    
    return {
        **budget.__dict__,
        "total_spent": total_spent,
        "remaining": remaining,
        "expenses_count": expenses_count,
    }


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new budget
    """
    new_budget = Budget(
        user_id=current_user.id,
        name=budget_data.name,
        amount=budget_data.amount,
        icon=budget_data.icon,
    )
    
    db.add(new_budget)
    await db.commit()
    await db.refresh(new_budget)
    
    return new_budget


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a budget
    """
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Update fields
    if budget_data.name is not None:
        budget.name = budget_data.name
    if budget_data.amount is not None:
        budget.amount = budget_data.amount
    if budget_data.icon is not None:
        budget.icon = budget_data.icon
    
    await db.commit()
    await db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a budget (cascades to expenses)
    """
    result = await db.execute(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        )
    )
    budget = result.scalar_one_or_none()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    await db.delete(budget)
    await db.commit()
    
    return None

