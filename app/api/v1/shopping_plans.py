"""
Shopping Plan API endpoints
"""

from datetime import date as date_type
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.shopping_plan import ShoppingItem, ShoppingPlan, ShoppingPlanStatus
from app.models.user import User
from app.schemas.shopping_plan import (
    ShoppingItemCreate,
    ShoppingItemResponse,
    ShoppingItemUpdate,
    ShoppingPlanCreate,
    ShoppingPlanResponse,
    ShoppingPlanUpdate,
    ShoppingPlanWithItems,
    StatusUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ShoppingPlanResponse])
async def list_shopping_plans(
    status_filter: Optional[ShoppingPlanStatus] = Query(None, alias="status", description="Filter by status"),
    start_date: Optional[date_type] = Query(None, description="Filter plans from this date"),
    end_date: Optional[date_type] = Query(None, description="Filter plans until this date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List shopping plans with optional filters
    """
    query = select(ShoppingPlan).where(ShoppingPlan.user_id == current_user.id)

    if status_filter:
        query = query.where(ShoppingPlan.status == status_filter)

    if start_date:
        query = query.where(ShoppingPlan.plan_date >= start_date)

    if end_date:
        query = query.where(ShoppingPlan.plan_date <= end_date)

    result = await db.execute(query.order_by(ShoppingPlan.plan_date.desc()))
    plans = result.scalars().all()

    return plans


@router.get("/{plan_id}", response_model=ShoppingPlanWithItems)
async def get_shopping_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get shopping plan with items
    """
    result = await db.execute(select(ShoppingPlan).where(ShoppingPlan.id == plan_id, ShoppingPlan.user_id == current_user.id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping plan not found")

    # Get items
    items_result = await db.execute(
        select(ShoppingItem).where(ShoppingItem.plan_id == plan_id).order_by(ShoppingItem.created_at.desc())
    )
    items = items_result.scalars().all()

    # Calculate totals
    total_estimated = sum(item.estimate_price for item in items)
    total_actual = sum(Decimal(str(item.actual_price)) if item.actual_price else Decimal(0) for item in items)

    return {
        **plan.__dict__,
        "items": items,
        "total_estimated": total_estimated,
        "total_actual": float(total_actual),
    }


@router.post("/", response_model=ShoppingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_shopping_plan(
    plan_data: ShoppingPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new shopping plan
    """
    new_plan = ShoppingPlan(
        user_id=current_user.id,
        plan_date=plan_data.plan_date,
        status=plan_data.status,
    )

    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)

    return new_plan


@router.patch("/{plan_id}", response_model=ShoppingPlanResponse)
async def update_shopping_plan(
    plan_id: int,
    plan_data: ShoppingPlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a shopping plan
    """
    result = await db.execute(select(ShoppingPlan).where(ShoppingPlan.id == plan_id, ShoppingPlan.user_id == current_user.id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping plan not found")

    if plan_data.plan_date is not None:
        plan.plan_date = plan_data.plan_date
    if plan_data.status is not None:
        plan.status = plan_data.status

    await db.commit()
    await db.refresh(plan)

    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_plan(
    plan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a shopping plan (cascades to items)
    """
    result = await db.execute(select(ShoppingPlan).where(ShoppingPlan.id == plan_id, ShoppingPlan.user_id == current_user.id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping plan not found")

    await db.delete(plan)
    await db.commit()

    return None


@router.post(
    "/{plan_id}/items/",
    response_model=ShoppingItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_shopping_item(
    plan_id: int,
    item_data: ShoppingItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add item to shopping plan
    """
    # Verify plan belongs to user
    plan_result = await db.execute(
        select(ShoppingPlan).where(ShoppingPlan.id == plan_id, ShoppingPlan.user_id == current_user.id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping plan not found")

    new_item = ShoppingItem(
        plan_id=plan_id,
        name=item_data.name,
        quantity=item_data.quantity,
        uom=item_data.uom,
        need_want=item_data.need_want,
        estimate_price=item_data.estimate_price,
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return new_item


@router.patch("/items/{item_id}", response_model=ShoppingItemResponse)
async def update_shopping_item(
    item_id: int,
    item_data: ShoppingItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a shopping item
    """
    result = await db.execute(
        select(ShoppingItem).join(ShoppingPlan).where(ShoppingItem.id == item_id, ShoppingPlan.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping item not found")

    # Update fields
    if item_data.name is not None:
        item.name = item_data.name
    if item_data.quantity is not None:
        item.quantity = item_data.quantity
    if item_data.uom is not None:
        item.uom = item_data.uom
    if item_data.need_want is not None:
        item.need_want = item_data.need_want
    if item_data.estimate_price is not None:
        item.estimate_price = item_data.estimate_price
    if item_data.actual_price is not None:
        item.actual_price = item_data.actual_price
    if item_data.is_purchased is not None:
        item.is_purchased = item_data.is_purchased
    if item_data.is_moved_to_next is not None:
        item.is_moved_to_next = item_data.is_moved_to_next
    if item_data.is_out_of_plan is not None:
        item.is_out_of_plan = item_data.is_out_of_plan

    await db.commit()
    await db.refresh(item)

    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a shopping item
    """
    result = await db.execute(
        select(ShoppingItem).join(ShoppingPlan).where(ShoppingItem.id == item_id, ShoppingPlan.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping item not found")

    await db.delete(item)
    await db.commit()

    return None


@router.patch("/{plan_id}/status", response_model=ShoppingPlanResponse)
async def update_plan_status(
    plan_id: int,
    status_data: StatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update shopping plan status
    """
    result = await db.execute(select(ShoppingPlan).where(ShoppingPlan.id == plan_id, ShoppingPlan.user_id == current_user.id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shopping plan not found")

    plan.status = status_data.status
    await db.commit()
    await db.refresh(plan)

    return plan
