"""
Saving Goal API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import date as date_type

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.saving_goal import SavingGoal, SavingContribution
from app.schemas.saving_goal import (
    SavingGoalCreate, SavingGoalUpdate, SavingGoalResponse, SavingGoalWithContributions,
    SavingContributionCreate, SavingContributionResponse
)

router = APIRouter()


@router.get("/", response_model=List[SavingGoalResponse])
async def list_saving_goals(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all saving goals for the current user
    """
    result = await db.execute(
        select(SavingGoal).where(SavingGoal.user_id == current_user.id)
        .order_by(SavingGoal.created_at.desc())
    )
    goals = result.scalars().all()
    return goals


@router.get("/{goal_id}", response_model=SavingGoalWithContributions)
async def get_saving_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get saving goal with contributions and progress
    """
    result = await db.execute(
        select(SavingGoal).where(
            SavingGoal.id == goal_id,
            SavingGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saving goal not found"
        )
    
    # Get contributions
    contributions_result = await db.execute(
        select(SavingContribution).where(SavingContribution.goal_id == goal_id)
        .order_by(SavingContribution.date.desc())
    )
    contributions = contributions_result.scalars().all()
    
    # Calculate totals and progress
    total_contributed_result = await db.execute(
        select(func.coalesce(func.sum(SavingContribution.amount), 0))
        .where(SavingContribution.goal_id == goal_id)
    )
    total_contributed = int(total_contributed_result.scalar_one() or 0)
    remaining_amount = max(0, goal.target_amount - total_contributed)
    progress_percentage = min(100, (total_contributed / goal.target_amount * 100) if goal.target_amount > 0 else 0)
    
    return {
        **goal.__dict__,
        "contributions": contributions,
        "total_contributed": total_contributed,
        "remaining_amount": remaining_amount,
        "progress_percentage": round(progress_percentage, 2),
    }


@router.post("/", response_model=SavingGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_saving_goal(
    goal_data: SavingGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new saving goal
    """
    new_goal = SavingGoal(
        user_id=current_user.id,
        title=goal_data.title,
        target_amount=goal_data.target_amount,
        target_date=goal_data.target_date,
    )
    
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)
    
    return new_goal


@router.patch("/{goal_id}", response_model=SavingGoalResponse)
async def update_saving_goal(
    goal_id: int,
    goal_data: SavingGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a saving goal
    """
    result = await db.execute(
        select(SavingGoal).where(
            SavingGoal.id == goal_id,
            SavingGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saving goal not found"
        )
    
    if goal_data.title is not None:
        goal.title = goal_data.title
    if goal_data.target_amount is not None:
        goal.target_amount = goal_data.target_amount
    if goal_data.target_date is not None:
        goal.target_date = goal_data.target_date
    
    await db.commit()
    await db.refresh(goal)
    
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saving_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a saving goal (cascades to contributions)
    """
    result = await db.execute(
        select(SavingGoal).where(
            SavingGoal.id == goal_id,
            SavingGoal.user_id == current_user.id
        )
    )
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saving goal not found"
        )
    
    await db.delete(goal)
    await db.commit()
    
    return None


@router.post("/{goal_id}/contributions/", response_model=SavingContributionResponse, status_code=status.HTTP_201_CREATED)
async def add_contribution(
    goal_id: int,
    contribution_data: SavingContributionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a contribution to a saving goal
    """
    # Verify goal belongs to user
    goal_result = await db.execute(
        select(SavingGoal).where(
            SavingGoal.id == goal_id,
            SavingGoal.user_id == current_user.id
        )
    )
    if not goal_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saving goal not found"
        )
    
    # Validate expense_id if provided
    if contribution_data.expense_id:
        from app.models.expense import Expense
        expense_result = await db.execute(
            select(Expense).where(
                Expense.id == contribution_data.expense_id,
                Expense.user_id == current_user.id
            )
        )
        if not expense_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
    
    new_contribution = SavingContribution(
        goal_id=goal_id,
        user_id=current_user.id,
        amount=contribution_data.amount,
        date=contribution_data.date,
        expense_id=contribution_data.expense_id,
    )
    
    db.add(new_contribution)
    await db.commit()
    await db.refresh(new_contribution)
    
    return new_contribution


@router.delete("/contributions/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contribution(
    contribution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a saving contribution
    """
    result = await db.execute(
        select(SavingContribution).join(SavingGoal).where(
            SavingContribution.id == contribution_id,
            SavingGoal.user_id == current_user.id
        )
    )
    contribution = result.scalar_one_or_none()
    
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    await db.delete(contribution)
    await db.commit()
    
    return None

