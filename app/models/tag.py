"""
Tag model - Global tags decoupled from budgets
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Tag(Base):
    """Global tag model - can be used across any budget/expense/income"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    color = Column(String(50), nullable=True)  # For UI customization
    description = Column(Text, nullable=True)  # For future AI context

    # AI metadata fields (for future use)
    ai_category = Column(String(100), nullable=True)  # AI-suggested category
    ai_keywords = Column(ARRAY(String), nullable=True)  # Keywords for AI matching
    usage_pattern = Column(JSONB, nullable=True)  # Usage statistics for AI

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="tags")
    expenses = relationship("Expense", back_populates="tag")
    incomes = relationship("Income", back_populates="tag")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_user_tag_name"),
        Index("idx_tag_user_id", "user_id"),
        Index("idx_tag_name", "name"),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name}, user_id={self.user_id})>"
