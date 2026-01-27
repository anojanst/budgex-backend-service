"""
Expense model
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Expense(Base):
    """Expense model"""
    
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id", ondelete="SET NULL"), nullable=True, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in cents/smallest unit
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="expenses")
    budget = relationship("Budget", back_populates="expenses")
    tag = relationship("Tag", back_populates="expenses")
    
    __table_args__ = (
        Index('idx_expense_user_id', 'user_id'),
        Index('idx_expense_budget_id', 'budget_id'),
        Index('idx_expense_tag_id', 'tag_id'),
        Index('idx_expense_date', 'date'),
        Index('idx_expense_user_date', 'user_id', 'date'),
    )
    
    def __repr__(self):
        return f"<Expense(id={self.id}, name={self.name}, amount={self.amount})>"

