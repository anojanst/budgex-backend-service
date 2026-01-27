"""
Balance History model
"""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class BalanceHistory(Base):
    """Balance history model for tracking daily balance"""

    __tablename__ = "balance_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    total_income = Column(Integer, nullable=False, default=0)
    total_expense = Column(Integer, nullable=False, default=0)
    balance = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="balance_history")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="unique_user_date"),
        Index("idx_balance_user_id", "user_id"),
        Index("idx_balance_date", "date"),
        Index("idx_balance_user_date", "user_id", "date"),
    )

    def __repr__(self):
        return f"<BalanceHistory(id={self.id}, date={self.date}, balance={self.balance})>"
