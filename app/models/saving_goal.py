"""
Saving Goal models
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SavingGoal(Base):
    """Saving goal model"""
    
    __tablename__ = "saving_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    target_amount = Column(Integer, nullable=False)  # Target amount in cents
    target_date = Column(Date, nullable=False, index=True)
    created_at = Column(Date, server_default=func.current_date(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="saving_goals")
    contributions = relationship("SavingContribution", back_populates="goal", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_saving_goal_user_id', 'user_id'),
        Index('idx_saving_goal_target_date', 'target_date'),
    )
    
    def __repr__(self):
        return f"<SavingGoal(id={self.id}, title={self.title}, target={self.target_amount})>"


class SavingContribution(Base):
    """Saving contribution model"""
    
    __tablename__ = "saving_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("saving_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Contribution amount in cents
    date = Column(Date, nullable=False, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(Date, server_default=func.current_date(), nullable=False)
    
    # Relationships
    goal = relationship("SavingGoal", back_populates="contributions")
    user = relationship("User", backref="saving_contributions")
    expense = relationship("Expense", foreign_keys=[expense_id])
    
    __table_args__ = (
        Index('idx_contribution_goal_id', 'goal_id'),
        Index('idx_contribution_user_id', 'user_id'),
        Index('idx_contribution_date', 'date'),
    )
    
    def __repr__(self):
        return f"<SavingContribution(id={self.id}, goal_id={self.goal_id}, amount={self.amount})>"

