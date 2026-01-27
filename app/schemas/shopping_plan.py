"""
Pydantic schemas for Shopping Plan API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date as date_type, datetime
from decimal import Decimal
from app.models.shopping_plan import ShoppingPlanStatus, NeedWant


class ShoppingItemBase(BaseModel):
    """Base shopping item schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Item name")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    uom: Optional[str] = Field(None, max_length=50, description="Unit of measure")
    need_want: NeedWant = Field(..., description="Need or want")
    estimate_price: int = Field(..., gt=0, description="Estimated price in cents")


class ShoppingItemCreate(ShoppingItemBase):
    """Schema for creating a shopping item"""
    pass


class ShoppingItemUpdate(BaseModel):
    """Schema for updating a shopping item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[Decimal] = Field(None, gt=0)
    uom: Optional[str] = Field(None, max_length=50)
    need_want: Optional[NeedWant] = None
    estimate_price: Optional[int] = Field(None, gt=0)
    actual_price: Optional[Decimal] = Field(None, ge=0)
    is_purchased: Optional[bool] = None
    is_moved_to_next: Optional[bool] = None
    is_out_of_plan: Optional[bool] = None


class ShoppingItemResponse(ShoppingItemBase):
    """Schema for shopping item response"""
    id: int
    plan_id: int
    actual_price: Optional[Decimal] = None
    is_purchased: bool = False
    is_moved_to_next: bool = False
    is_out_of_plan: bool = False
    created_at: date_type
    
    class Config:
        from_attributes = True


class ShoppingPlanBase(BaseModel):
    """Base shopping plan schema"""
    plan_date: date_type = Field(..., description="Shopping plan date")
    status: ShoppingPlanStatus = Field(default=ShoppingPlanStatus.DRAFT, description="Plan status")


class ShoppingPlanCreate(ShoppingPlanBase):
    """Schema for creating a shopping plan"""
    pass


class ShoppingPlanUpdate(BaseModel):
    """Schema for updating a shopping plan"""
    plan_date: Optional[date_type] = None
    status: Optional[ShoppingPlanStatus] = None


class ShoppingPlanResponse(ShoppingPlanBase):
    """Schema for shopping plan response"""
    id: int
    user_id: str
    created_at: date_type
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShoppingPlanWithItems(ShoppingPlanResponse):
    """Shopping plan with items"""
    items: List[ShoppingItemResponse] = Field(default_factory=list)
    total_estimated: int = Field(0, description="Total estimated cost in cents")
    total_actual: Decimal = Field(0, description="Total actual cost")
    
    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    """Schema for updating plan status"""
    status: ShoppingPlanStatus

