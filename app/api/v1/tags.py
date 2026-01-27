"""
Tag API endpoints (Global Tags)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.tag import Tag
from app.models.expense import Expense
from app.models.income import Income
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagWithStats

router = APIRouter()


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    budget_id: Optional[int] = Query(None, description="Filter tags used in a specific budget"),
    used_with: Optional[str] = Query(None, description="Filter by usage: 'expenses', 'incomes', or 'both'"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all global tags for the current user
    
    - **budget_id**: Optional filter to show tags used in a specific budget
    - **used_with**: Optional filter by usage type ('expenses', 'incomes', 'both')
    """
    query = select(Tag).where(Tag.user_id == current_user.id)
    
    # Filter by budget_id if provided
    if budget_id:
        # Get tag IDs used in expenses for this budget
        expense_tags_query = select(distinct(Expense.tag_id)).where(
            Expense.budget_id == budget_id,
            Expense.tag_id.isnot(None)
        )
        expense_tags_result = await db.execute(expense_tags_query)
        expense_tag_ids = [tag_id for tag_id, in expense_tags_result.all() if tag_id]
        
        # Get tag IDs used in incomes (incomes don't have budget_id, so we check all)
        # For now, if budget_id is provided, we only show tags from expenses
        query = query.where(Tag.id.in_(expense_tag_ids))
    
    # Filter by usage type
    if used_with == "expenses":
        expense_tags_query = select(distinct(Expense.tag_id)).where(
            Expense.tag_id.isnot(None),
            Expense.user_id == current_user.id
        )
        expense_tags_result = await db.execute(expense_tags_query)
        expense_tag_ids = [tag_id for tag_id, in expense_tags_result.all() if tag_id]
        query = query.where(Tag.id.in_(expense_tag_ids))
    elif used_with == "incomes":
        income_tags_query = select(distinct(Income.tag_id)).where(
            Income.tag_id.isnot(None),
            Income.user_id == current_user.id
        )
        income_tags_result = await db.execute(income_tags_query)
        income_tag_ids = [tag_id for tag_id, in income_tags_result.all() if tag_id]
        query = query.where(Tag.id.in_(income_tag_ids))
    elif used_with == "both":
        # Tags used in both expenses and incomes
        expense_tags_query = select(distinct(Expense.tag_id)).where(
            Expense.tag_id.isnot(None),
            Expense.user_id == current_user.id
        )
        expense_tags_result = await db.execute(expense_tags_query)
        expense_tag_ids = set(tag_id for tag_id, in expense_tags_result.all() if tag_id)
        
        income_tags_query = select(distinct(Income.tag_id)).where(
            Income.tag_id.isnot(None),
            Income.user_id == current_user.id
        )
        income_tags_result = await db.execute(income_tags_query)
        income_tag_ids = set(tag_id for tag_id, in income_tags_result.all() if tag_id)
        
        both_tag_ids = list(expense_tag_ids & income_tag_ids)
        query = query.where(Tag.id.in_(both_tag_ids))
    
    result = await db.execute(query.order_by(Tag.created_at.desc()))
    tags = result.scalars().all()
    
    return tags


@router.get("/{tag_id}", response_model=TagWithStats)
async def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tag details with usage statistics
    """
    result = await db.execute(
        select(Tag).where(
            Tag.id == tag_id,
            Tag.user_id == current_user.id
        )
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Get expense statistics
    expense_stats_result = await db.execute(
        select(
            func.count(Expense.id).label("expenses_count"),
            func.coalesce(func.sum(Expense.amount), 0).label("total_spent")
        ).where(
            Expense.tag_id == tag_id,
            Expense.user_id == current_user.id
        )
    )
    expense_stats = expense_stats_result.first()
    
    # Get unique budget IDs separately
    budget_ids_result = await db.execute(
        select(distinct(Expense.budget_id)).where(
            Expense.tag_id == tag_id,
            Expense.user_id == current_user.id,
            Expense.budget_id.isnot(None)
        )
    )
    budget_ids = [bid for bid, in budget_ids_result.all() if bid is not None]
    
    # Get income statistics
    income_stats_result = await db.execute(
        select(
            func.count(Income.id).label("incomes_count"),
            func.coalesce(func.sum(Income.amount), 0).label("total_earned")
        ).where(
            Income.tag_id == tag_id,
            Income.user_id == current_user.id
        )
    )
    income_stats = income_stats_result.first()
    
    expenses_count = expense_stats.expenses_count or 0
    incomes_count = income_stats.incomes_count or 0
    total_spent = int(expense_stats.total_spent) if expense_stats.total_spent else 0
    total_earned = int(income_stats.total_earned) if income_stats.total_earned else 0
    
    return {
        **tag.__dict__,
        "expenses_count": expenses_count,
        "incomes_count": incomes_count,
        "total_spent": total_spent,
        "total_earned": total_earned,
        "budgets_used_in": budget_ids,
    }


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new global tag (not tied to any budget)
    """
    # Check if tag name already exists for this user
    existing_result = await db.execute(
        select(Tag).where(
            Tag.user_id == current_user.id,
            Tag.name == tag_data.name
        )
    )
    existing_tag = existing_result.scalar_one_or_none()
    
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{tag_data.name}' already exists"
        )
    
    new_tag = Tag(
        user_id=current_user.id,
        name=tag_data.name,
        color=tag_data.color,
        description=tag_data.description,
    )
    
    db.add(new_tag)
    await db.commit()
    await db.refresh(new_tag)
    
    return new_tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a tag (name, color, description)
    """
    result = await db.execute(
        select(Tag).where(
            Tag.id == tag_id,
            Tag.user_id == current_user.id
        )
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Check if new name conflicts with existing tag
    if tag_data.name and tag_data.name != tag.name:
        existing_result = await db.execute(
            select(Tag).where(
                Tag.user_id == current_user.id,
                Tag.name == tag_data.name,
                Tag.id != tag_id
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag_data.name}' already exists"
            )
    
    # Update fields
    if tag_data.name is not None:
        tag.name = tag_data.name
    if tag_data.color is not None:
        tag.color = tag_data.color
    if tag_data.description is not None:
        tag.description = tag_data.description
    
    await db.commit()
    await db.refresh(tag)
    
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tag (check if used, warn or prevent)
    """
    result = await db.execute(
        select(Tag).where(
            Tag.id == tag_id,
            Tag.user_id == current_user.id
        )
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Check if tag is used in expenses or incomes
    expense_count_result = await db.execute(
        select(func.count(Expense.id)).where(Expense.tag_id == tag_id)
    )
    expense_count = expense_count_result.scalar_one()
    
    income_count_result = await db.execute(
        select(func.count(Income.id)).where(Income.tag_id == tag_id)
    )
    income_count = income_count_result.scalar_one()
    
    if expense_count > 0 or income_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tag: it is used in {expense_count} expense(s) and {income_count} income(s). "
                   f"Please remove the tag from all expenses and incomes first."
        )
    
    await db.delete(tag)
    await db.commit()
    
    return None

