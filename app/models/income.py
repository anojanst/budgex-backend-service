"""
Income model
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class IncomeCategory(str, enum.Enum):
    """Income category enum"""
    SALARY = "Salary"
    RENTAL = "Rental"
    INVESTMENTS = "Investments"
    FREELANCE = "Freelance"
    GIFTS = "Gifts"
    OTHER = "Other"


class Income(Base):
    """Income model"""
    
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in cents/smallest unit
    category = Column(Enum(IncomeCategory), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="SET NULL"), nullable=True, index=True)  # NEW: Tags can be attached to incomes
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="incomes")
    tag = relationship("Tag", back_populates="incomes")
    
    __table_args__ = (
        Index('idx_income_user_id', 'user_id'),
        Index('idx_income_tag_id', 'tag_id'),
        Index('idx_income_date', 'date'),
        Index('idx_income_category', 'category'),
        Index('idx_income_user_date', 'user_id', 'date'),
    )
    
    def __repr__(self):
        return f"<Income(id={self.id}, name={self.name}, amount={self.amount})>"

