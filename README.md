# BudgeX Backend Service

FastAPI backend service for the BudgeX mobile application.

## Features

- **UUID-based user identification** with email OTP authentication
- **JWT-based authentication** with long-lived sessions
- **Global tags system** (decoupled from budgets)
- **Comprehensive budget tracking** (budgets, expenses, incomes, loans, shopping plans, saving goals)
- **AI/ML ready architecture** for future enhancements
- **MCP tools support** for AI-assisted features

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (async with SQLAlchemy)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Email**: FastAPI-Mail / aiosmtplib
- **Validation**: Pydantic

## Project Structure

```
budgex-backend-service/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection & session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   ├── core/                # Core functionality (security, config)
│   ├── utils/               # Utility functions
│   └── services/            # Business logic services (AI/ML)
├── alembic/                 # Database migrations
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Update the following in `.env`:
- `DATABASE_URL`: Your PostgreSQL connection string
- `SECRET_KEY`: Generate a secure secret key (min 32 characters)
- `SMTP_*`: Your email server configuration

### 4. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE budgex_mobile_db;
```

Run migrations:

```bash
alembic upgrade head
```

### 5. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback:

```bash
alembic downgrade -1
```

## API Endpoints

### Authentication (Simplified - 2 endpoints)
- `POST /api/v1/auth/send-otp` - Send OTP to email (works for both registration and login)
- `POST /api/v1/auth/verify-otp` - Verify OTP and authenticate (auto-creates user if doesn't exist)

### Resources
- `/api/v1/budgets/` - Budget management
- `/api/v1/expenses/` - Expense management
- `/api/v1/incomes/` - Income management
- `/api/v1/tags/` - Global tag management
- `/api/v1/loans/` - Loan management
- `/api/v1/shopping-plans/` - Shopping plan management
- `/api/v1/saving-goals/` - Saving goal management
- `/api/v1/dashboard/` - Dashboard summaries and charts

## Environment Variables

See `.env.example` for all available configuration options.

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions to:
- **Railway** (Recommended - easiest setup)
- **Render** (Free tier available)
- **Fly.io** (Global edge deployment)
- Docker and other platforms

### Quick Deploy with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) automatically:
- Lints code on push/PR
- Runs tests
- Builds Docker image

## License

[Your License Here]

