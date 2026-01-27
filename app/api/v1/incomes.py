"""
Income API endpoints
"""

from datetime import date as date_type
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.income import Income, IncomeCategory
from app.models.tag import Tag
from app.models.user import User
from app.schemas.income import IncomeCreate, IncomeResponse, IncomeUpdate, IncomeWithTag

router = APIRouter()


@router.get("/", response_model=List[IncomeWithTag])
async def list_incomes(
    category: Optional[IncomeCategory] = Query(None, description="Filter by category"),
    tag_id: Optional[int] = Query(None, description="Filter by tag ID"),
    start_date: Optional[date_type] = Query(None, description="Filter incomes from this date"),
    end_date: Optional[date_type] = Query(None, description="Filter incomes until this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List incomes with optional filters

    - **category**: Filter by income category
    - **tag_id**: Filter by tag
    - **start_date**: Filter incomes from this date
    - **end_date**: Filter incomes until this date
    """
    query = select(Income).where(Income.user_id == current_user.id)

    if category:
        query = query.where(Income.category == category)

    if tag_id:
        query = query.where(Income.tag_id == tag_id)

    if start_date:
        query = query.where(Income.date >= start_date)

    if end_date:
        query = query.where(Income.date <= end_date)

    result = await db.execute(query.order_by(Income.date.desc(), Income.created_at.desc()))
    incomes = result.scalars().all()

    # Load related tag info
    incomes_with_tag = []
    for income in incomes:
        income_dict = {
            **income.__dict__,
            "tag_name": None,
            "tag_color": None,
        }

        if income.tag_id:
            tag_result = await db.execute(select(Tag).where(Tag.id == income.tag_id))
            tag = tag_result.scalar_one_or_none()
            if tag:
                income_dict["tag_name"] = tag.name
                income_dict["tag_color"] = tag.color

        incomes_with_tag.append(income_dict)

    return incomes_with_tag


@router.get("/{income_id}", response_model=IncomeWithTag)
async def get_income(
    income_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get income details
    """
    result = await db.execute(select(Income).where(Income.id == income_id, Income.user_id == current_user.id))
    income = result.scalar_one_or_none()

    if not income:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")

    income_dict = {
        **income.__dict__,
        "tag_name": None,
        "tag_color": None,
    }

    if income.tag_id:
        tag_result = await db.execute(select(Tag).where(Tag.id == income.tag_id))
        tag = tag_result.scalar_one_or_none()
        if tag:
            income_dict["tag_name"] = tag.name
            income_dict["tag_color"] = tag.color

    return income_dict


@router.post("/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
async def create_income(
    income_data: IncomeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new income (with optional tag_id)
    """
    # Validate tag_id if provided
    if income_data.tag_id:
        tag_result = await db.execute(select(Tag).where(Tag.id == income_data.tag_id, Tag.user_id == current_user.id))
        if not tag_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Convert 0 to None for optional foreign keys
    tag_id = income_data.tag_id if income_data.tag_id else None

    new_income = Income(
        user_id=current_user.id,
        name=income_data.name,
        amount=income_data.amount,
        category=income_data.category,
        date=income_data.date,
        tag_id=tag_id,
    )

    db.add(new_income)
    await db.commit()
    await db.refresh(new_income)

    return new_income


@router.patch("/{income_id}", response_model=IncomeResponse)
async def update_income(
    income_id: int,
    income_data: IncomeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an income (including tag_id)
    """
    result = await db.execute(select(Income).where(Income.id == income_id, Income.user_id == current_user.id))
    income = result.scalar_one_or_none()

    if not income:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")

    # Validate tag_id if provided
    if income_data.tag_id is not None:
        if income_data.tag_id:
            tag_result = await db.execute(select(Tag).where(Tag.id == income_data.tag_id, Tag.user_id == current_user.id))
            if not tag_result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    # Update fields
    if income_data.name is not None:
        income.name = income_data.name
    if income_data.amount is not None:
        income.amount = income_data.amount
    if income_data.category is not None:
        income.category = income_data.category
    if income_data.date is not None:
        income.date = income_data.date
    if income_data.tag_id is not None:
        income.tag_id = income_data.tag_id if income_data.tag_id else None

    await db.commit()
    await db.refresh(income)

    return income


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an income
    """
    result = await db.execute(select(Income).where(Income.id == income_id, Income.user_id == current_user.id))
    income = result.scalar_one_or_none()

    if not income:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")

    await db.delete(income)
    await db.commit()

    return None
