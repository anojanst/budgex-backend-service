"""
SQLAlchemy database models
"""

from app.models.user import User
from app.models.otp import OTP
from app.models.budget import Budget
from app.models.tag import Tag
from app.models.expense import Expense
from app.models.income import Income, IncomeCategory
from app.models.balance_history import BalanceHistory
from app.models.loan import Loan, LoanRepayment
from app.models.shopping_plan import ShoppingPlan, ShoppingItem, ShoppingPlanStatus, NeedWant
from app.models.saving_goal import SavingGoal, SavingContribution

__all__ = [
    "User",
    "OTP",
    "Budget",
    "Tag",
    "Expense",
    "Income",
    "IncomeCategory",
    "BalanceHistory",
    "Loan",
    "LoanRepayment",
    "ShoppingPlan",
    "ShoppingItem",
    "ShoppingPlanStatus",
    "NeedWant",
    "SavingGoal",
    "SavingContribution",
]
