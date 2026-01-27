"""
Loan models
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Loan(Base):
    """Loan model"""
    
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lender = Column(String(255), nullable=False)
    principal_amount = Column(Integer, nullable=False)  # Amount in cents
    remaining_principal = Column(Integer, nullable=False)  # Amount in cents
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Percentage with 2 decimal places
    tenure_months = Column(Integer, nullable=False)
    repayment_frequency = Column(String(50), nullable=False)  # e.g., 'monthly', 'weekly'
    emi = Column(Integer, nullable=False)  # EMI amount in cents
    next_due_date = Column(Date, nullable=False, index=True)
    is_paid_off = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="loans")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_loan_user_id', 'user_id'),
        Index('idx_loan_next_due_date', 'next_due_date'),
    )
    
    def __repr__(self):
        return f"<Loan(id={self.id}, lender={self.lender}, principal={self.principal_amount})>"


class LoanRepayment(Base):
    """Loan repayment model"""
    
    __tablename__ = "loan_repayments"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Total payment amount in cents
    principal_amount = Column(Integer, nullable=False)  # Principal portion in cents
    interest_amount = Column(Integer, nullable=False)  # Interest portion in cents
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'paid', 'overdue'
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    loan = relationship("Loan", back_populates="repayments")
    user = relationship("User", backref="loan_repayments")
    expense = relationship("Expense", foreign_keys=[expense_id])
    
    __table_args__ = (
        Index('idx_repayment_loan_id', 'loan_id'),
        Index('idx_repayment_user_id', 'user_id'),
        Index('idx_repayment_scheduled_date', 'scheduled_date'),
        Index('idx_repayment_status', 'status'),
    )
    
    def __repr__(self):
        return f"<LoanRepayment(id={self.id}, loan_id={self.loan_id}, amount={self.amount})>"

