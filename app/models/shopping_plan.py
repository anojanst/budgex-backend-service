"""
Shopping Plan models
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ShoppingPlanStatus(str, enum.Enum):
    """Shopping plan status enum"""

    DRAFT = "draft"
    READY = "ready"
    SHOPPING = "shopping"
    POST_SHOPPING = "post_shopping"
    COMPLETED = "completed"


class NeedWant(str, enum.Enum):
    """Need/Want enum"""

    NEED = "need"
    WANT = "want"


class ShoppingPlan(Base):
    """Shopping plan model"""

    __tablename__ = "shopping_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_date = Column(Date, nullable=False, index=True)
    status = Column(Enum(ShoppingPlanStatus), nullable=False, default=ShoppingPlanStatus.DRAFT)
    created_at = Column(Date, server_default=func.current_date(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="shopping_plans")
    items = relationship("ShoppingItem", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_shopping_plan_user_id", "user_id"),
        Index("idx_shopping_plan_date", "plan_date"),
        Index("idx_shopping_plan_status", "status"),
    )

    def __repr__(self):
        return f"<ShoppingPlan(id={self.id}, plan_date={self.plan_date}, status={self.status})>"


class ShoppingItem(Base):
    """Shopping item model"""

    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(
        Integer,
        ForeignKey("shopping_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    uom = Column(String(50), nullable=True)  # Unit of measure (e.g., 'kg', 'pieces')
    need_want = Column(Enum(NeedWant), nullable=False)
    estimate_price = Column(Integer, nullable=False)  # Estimated price in cents
    actual_price = Column(Numeric(10, 2), nullable=True)  # Actual price (can have decimals)
    is_purchased = Column(Boolean, default=False, nullable=False)
    is_moved_to_next = Column(Boolean, default=False, nullable=False)
    is_out_of_plan = Column(Boolean, default=False, nullable=False)
    created_at = Column(Date, server_default=func.current_date(), nullable=False)

    # Relationships
    plan = relationship("ShoppingPlan", back_populates="items")

    __table_args__ = (Index("idx_shopping_item_plan_id", "plan_id"),)

    def __repr__(self):
        return f"<ShoppingItem(id={self.id}, name={self.name}, plan_id={self.plan_id})>"
