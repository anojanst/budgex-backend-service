"""
Dashboard API endpoints
"""

from datetime import date as date_type

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.income import Income
from app.models.loan import Loan, LoanRepayment
from app.models.saving_goal import SavingContribution, SavingGoal
from app.models.user import User
from app.schemas.dashboard import (
    BudgetSummaryAggregate,
    DashboardSummary,
    IncomeExpenseSummary,
    LoanSummaryAggregate,
    SavingGoalsSummary,
)
from app.schemas.loan import PaymentDueSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard summary:

    - Total budgets, spent, remaining
    - Total income, expenses, balance
    - Active loans count, total EMI, payments due
    - Active saving goals, total progress
    """
    today = date_type.today()

    # ---- Budgets aggregate ----
    budget_result = await db.execute(
        select(
            func.count(Budget.id).label("total_budgets"),
            func.coalesce(func.sum(Budget.amount), 0).label("total_budget_amount"),
        ).where(Budget.user_id == current_user.id)
    )
    budget_row = budget_result.first()
    total_budgets = budget_row.total_budgets or 0
    total_budget_amount = int(budget_row.total_budget_amount or 0)

    # Total spent in budgets is just all expenses for this user
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == current_user.id)
    )
    total_spent = int(expense_result.scalar_one() or 0)
    total_remaining = total_budget_amount - total_spent

    budgets_summary = BudgetSummaryAggregate(
        total_budgets=total_budgets,
        total_budget_amount=total_budget_amount,
        total_spent=total_spent,
        total_remaining=total_remaining,
    )

    # ---- Income / Expense summary ----
    income_result = await db.execute(
        select(func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == current_user.id)
    )
    total_income = int(income_result.scalar_one() or 0)

    expense_total_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == current_user.id)
    )
    total_expense = int(expense_total_result.scalar_one() or 0)

    income_expense_summary = IncomeExpenseSummary(
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
    )

    # ---- Loans summary ----
    loans_result = await db.execute(
        select(
            func.count(Loan.id).label("active_loans_count"),
            func.coalesce(func.sum(Loan.emi), 0).label("total_emi"),
        ).where(Loan.user_id == current_user.id, Loan.is_paid_off.is_(False))
    )
    loans_row = loans_result.first()
    active_loans_count = loans_row.active_loans_count or 0
    total_emi = int(loans_row.total_emi or 0)

    # Payments due (reuse logic from /loans/payments-due)
    payments_due_result = await db.execute(
        select(
            func.count(LoanRepayment.id).label("count"),
            func.coalesce(func.sum(LoanRepayment.amount), 0).label("total_amount"),
        )
        .select_from(LoanRepayment)
        .join(Loan)
        .where(
            Loan.user_id == current_user.id,
            LoanRepayment.status != "paid",
            LoanRepayment.scheduled_date <= today,
        )
    )
    payments_due_row = payments_due_result.first()
    payments_due = PaymentDueSummary(
        count=payments_due_row.count or 0,
        total_amount=int(payments_due_row.total_amount or 0),
    )

    loans_summary = LoanSummaryAggregate(
        active_loans_count=active_loans_count,
        total_emi=total_emi,
        payments_due=payments_due,
    )

    # ---- Saving goals summary ----
    # Active goals: for now, treat all user goals as active
    goals_result = await db.execute(
        select(
            func.count(SavingGoal.id).label("goals_count"),
            func.coalesce(func.sum(SavingGoal.target_amount), 0).label("total_target_amount"),
        ).where(SavingGoal.user_id == current_user.id)
    )
    goals_row = goals_result.first()
    active_goals_count = goals_row.goals_count or 0
    total_target_amount = int(goals_row.total_target_amount or 0)

    contributions_result = await db.execute(
        select(func.coalesce(func.sum(SavingContribution.amount), 0)).where(
            SavingContribution.user_id == current_user.id
        )
    )
    total_contributed = int(contributions_result.scalar_one() or 0)

    if total_target_amount > 0:
        overall_progress_percentage = min(100.0, (total_contributed / total_target_amount) * 100)
    else:
        overall_progress_percentage = 0.0

    saving_goals_summary = SavingGoalsSummary(
        active_goals_count=active_goals_count,
        total_target_amount=total_target_amount,
        total_contributed=total_contributed,
        overall_progress_percentage=round(overall_progress_percentage, 2),
    )

    return DashboardSummary(
        date=today,
        budgets=budgets_summary,
        income_expense=income_expense_summary,
        loans=loans_summary,
        saving_goals=saving_goals_summary,
    )


