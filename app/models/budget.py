"""
Budget model
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Budget(Base):
    """Budget model"""

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in cents/smallest unit
    icon = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="budgets")
    expenses = relationship("Expense", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_budget_user_id", "user_id"),)

    def __repr__(self):
        return f"<Budget(id={self.id}, name={self.name}, amount={self.amount})>"
