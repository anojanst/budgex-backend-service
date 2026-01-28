"""
Pydantic schemas for Dashboard API
"""

from datetime import date as date_type
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.loan import PaymentDueSummary


class BudgetSummaryAggregate(BaseModel):
    """Aggregate summary for budgets."""

    total_budgets: int = Field(..., ge=0, description="Number of budgets")
    total_budget_amount: int = Field(..., ge=0, description="Total budgeted amount in cents")
    total_spent: int = Field(..., ge=0, description="Total spent across all budgets in cents")
    total_remaining: int = Field(..., description="Total remaining across all budgets in cents")


class IncomeExpenseSummary(BaseModel):
    """Aggregate income/expense/balance summary."""

    total_income: int = Field(..., ge=0, description="Total income in cents")
    total_expense: int = Field(..., ge=0, description="Total expenses in cents")
    balance: int = Field(..., description="Balance (income - expenses) in cents")


class LoanSummaryAggregate(BaseModel):
    """Aggregate summary for loans."""

    active_loans_count: int = Field(..., ge=0, description="Number of active (not paid off) loans")
    total_emi: int = Field(..., ge=0, description="Total EMI for active loans in cents")
    payments_due: PaymentDueSummary


class SavingGoalsSummary(BaseModel):
    """Aggregate summary for saving goals."""

    active_goals_count: int = Field(..., ge=0, description="Number of active saving goals")
    total_target_amount: int = Field(..., ge=0, description="Total target amount across goals in cents")
    total_contributed: int = Field(..., ge=0, description="Total contributed across goals in cents")
    overall_progress_percentage: float = Field(
        ..., ge=0, le=100, description="Overall progress percentage across all saving goals"
    )


class DashboardSummary(BaseModel):
    """Main dashboard summary schema."""

    date: date_type = Field(..., description="The date for which the summary is calculated")
    budgets: BudgetSummaryAggregate
    income_expense: IncomeExpenseSummary
    loans: LoanSummaryAggregate
    saving_goals: SavingGoalsSummary


class BudgetComparisonItem(BaseModel):
    """Single budget entry for comparison chart."""

    budget_id: int
    name: str
    amount: int = Field(..., ge=0, description="Budget amount in cents")
    total_spent: int = Field(..., ge=0, description="Total spent in this budget in cents")
    remaining: int = Field(..., description="Remaining amount in this budget in cents")


class BudgetComparisonChart(BaseModel):
    """Budget comparison chart data."""

    items: List[BudgetComparisonItem] = Field(default_factory=list)


class BudgetPieSlice(BaseModel):
    """Slice of the budget pie chart."""

    label: str = Field(..., description="Budget name or 'Unassigned'")
    amount: int = Field(..., ge=0, description="Total spent amount in cents")


class BudgetPieChart(BaseModel):
    """Budget pie chart data."""

    slices: List[BudgetPieSlice] = Field(default_factory=list)


class IncomeExpenseBalancePoint(BaseModel):
    """Single data point for income-expense-balance chart."""

    date: date_type
    income: int = Field(..., ge=0, description="Income amount in cents for this date")
    expense: int = Field(..., ge=0, description="Expense amount in cents for this date")
    balance: int = Field(..., description="Net balance (income - expense) for this date in cents")


class IncomeExpenseBalanceChart(BaseModel):
    """Line chart data for income, expense and balance over time."""

    points: List[IncomeExpenseBalancePoint] = Field(default_factory=list)



