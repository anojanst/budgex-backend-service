"""
FastAPI application entry point
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import get_db

app = FastAPI(
    title="BudgeX API",
    description="Backend API for BudgeX mobile application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BudgeX API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/health/db")
async def database_health_check():
    """Database health check endpoint"""
    try:
        from sqlalchemy import text
        from app.database import get_engine
        
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


# Include API routers
from app.api.v1 import auth, users, budgets, tags, expenses, incomes, loans, shopping_plans, saving_goals, balance_history

app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["auth"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["users"])
app.include_router(budgets.router, prefix=f"{settings.API_V1_PREFIX}/budgets", tags=["budgets"])
app.include_router(tags.router, prefix=f"{settings.API_V1_PREFIX}/tags", tags=["tags"])
app.include_router(expenses.router, prefix=f"{settings.API_V1_PREFIX}/expenses", tags=["expenses"])
app.include_router(incomes.router, prefix=f"{settings.API_V1_PREFIX}/incomes", tags=["incomes"])
app.include_router(loans.router, prefix=f"{settings.API_V1_PREFIX}/loans", tags=["loans"])
app.include_router(shopping_plans.router, prefix=f"{settings.API_V1_PREFIX}/shopping-plans", tags=["shopping-plans"])
app.include_router(saving_goals.router, prefix=f"{settings.API_V1_PREFIX}/saving-goals", tags=["saving-goals"])
app.include_router(balance_history.router, prefix=f"{settings.API_V1_PREFIX}/balance-history", tags=["balance-history"])


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

