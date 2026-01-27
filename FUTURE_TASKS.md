# BudgeX Backend Service - Future & Optional Tasks

This document contains optional features and future enhancements that can be implemented as needed.

---

## Optional Features

### Authentication Enhancements
- [ ] `POST /api/v1/auth/refresh` - Refresh access token (if using refresh tokens)
  - Request: `{ "refresh_token": "..." }`
  - Response: `{ "access_token": "...", "token_type": "bearer" }`
  - Note: Currently using long-lived tokens (30 days), refresh tokens are optional

- [ ] `POST /api/v1/auth/logout` - Logout (invalidate token)
  - Request: Bearer token in header
  - Response: `{ "message": "Logged out successfully" }`
  - Note: Currently tokens expire naturally, explicit logout is optional

### Rate Limiting
- [ ] Rate limiting for OTP requests (prevent abuse)
  - Max 3 requests per email per hour for registration
  - Max 5 requests per email per hour for login
  - Implement using middleware (e.g., `slowapi` or Redis-based rate limiting)

### Dashboard/Summary API
- [ ] `GET /api/v1/dashboard/summary` - Get dashboard summary:
  - Total budgets, spent, remaining
  - Total income, expenses, balance
  - Active loans count, total EMI
  - Active saving goals, total progress

- [ ] `GET /api/v1/dashboard/charts/budget-comparison` - Budget comparison data
- [ ] `GET /api/v1/dashboard/charts/pie-chart` - Budget pie chart data
- [ ] `GET /api/v1/dashboard/charts/income-expense-balance` - Line chart data

**Note**: These endpoints can be added when mobile app needs dashboard data aggregation.

### Balance History Auto-Update
- [ ] Auto-update balance history on income/expense changes
  - Implement background task or database triggers
  - Update balance history when income/expense is created/updated/deleted
  - Handle edge cases (negative balances, date gaps)

---

## Future AI/ML Features

### Phase 7: AI/ML Architecture & Scalability

#### 7.1 Architecture for AI/ML Integration
- [ ] Design modular service architecture:
  - Core business logic layer (separated from API layer)
  - Service layer for AI/ML operations
  - Plugin/extension system for MCP tools
- [ ] Create abstraction layer for AI services:
  - `app/services/ai/` directory structure
  - `app/services/ai/base.py` - Base AI service interface
  - `app/services/ai/budget_advisor.py` - Budget recommendations
  - `app/services/ai/expense_categorizer.py` - Auto-categorization
  - `app/services/ai/insights_generator.py` - Financial insights
- [ ] Design for MCP (Model Context Protocol) tools:
  - `app/services/mcp/` directory
  - `app/services/mcp/tools/` - MCP tool implementations
  - `app/services/mcp/registry.py` - Tool registry
  - `app/services/mcp/executor.py` - Tool execution engine

#### 7.2 Data Models for AI Context
- [ ] **AIInsights Model** (for storing AI-generated insights):
  - `id` (SERIAL, primary key)
  - `user_id` (UUID, FK to users, NOT NULL)
  - `insight_type` (VARCHAR: 'budget_recommendation', 'spending_pattern', 'savings_opportunity', etc.)
  - `title` (VARCHAR, NOT NULL)
  - `description` (TEXT, NOT NULL)
  - `confidence_score` (NUMERIC(3,2), nullable)
  - `metadata` (JSONB, nullable) - Store AI context, model info, etc.
  - `is_applied` (BOOLEAN, default: false)
  - `created_at` (TIMESTAMP)
  - `expires_at` (TIMESTAMP, nullable)

- [ ] **AIActions Model** (for tracking AI-assisted actions):
  - `id` (SERIAL, primary key)
  - `user_id` (UUID, FK to users, NOT NULL)
  - `action_type` (VARCHAR: 'auto_categorize', 'suggest_budget', 'detect_anomaly', etc.)
  - `entity_type` (VARCHAR: 'expense', 'income', 'budget', etc.)
  - `entity_id` (INTEGER, nullable)
  - `suggested_value` (JSONB, nullable) - Store AI suggestions
  - `user_action` (VARCHAR: 'accepted', 'rejected', 'modified', 'pending')
  - `metadata` (JSONB, nullable)
  - `created_at` (TIMESTAMP)

- [ ] **TagMetadata Model** (for AI context on tags):
  - Extend Tags model with:
  - `ai_category` (VARCHAR, nullable) - AI-suggested category
  - `ai_keywords` (TEXT[], nullable) - Keywords for AI matching
  - `usage_pattern` (JSONB, nullable) - Store usage statistics for AI
  - **Note**: These fields already exist in the Tag model, ready for AI integration

#### 7.3 API Endpoints for AI Features
- [ ] `POST /api/v1/ai/categorize-expense` - Auto-categorize expense using AI
- [ ] `POST /api/v1/ai/suggest-budget` - Get AI budget recommendations
- [ ] `POST /api/v1/ai/analyze-spending` - Analyze spending patterns
- [ ] `GET /api/v1/ai/insights` - Get AI-generated insights
- [ ] `POST /api/v1/ai/insights/{insight_id}/apply` - Apply AI insight
- [ ] `GET /api/v1/ai/actions` - Get AI action history
- [ ] `POST /api/v1/mcp/tools/execute` - Execute MCP tool

#### 7.4 Scalability Considerations
- [ ] Design for async processing:
  - Background tasks for AI operations
  - Queue system (Redis/Celery) for heavy AI tasks
- [ ] Caching strategy:
  - Cache frequently accessed data (tags, budgets summary)
  - Cache AI insights (with TTL)
- [ ] Database indexing:
  - Index on `user_id` + `insight_type` for AI insights
  - JSONB indexes for metadata fields
- [ ] API versioning:
  - Keep `/api/v1/` for stable endpoints
  - Use `/api/v2/` or `/api/ai/` for AI features
- [ ] Rate limiting:
  - Different limits for AI endpoints
  - Per-user AI request quotas

---

## Business Logic Enhancements

### Loan Management
- [ ] EMI calculation logic
- [ ] Interest calculation
- [ ] Principal reduction on payments
- [ ] Extra payment handling
- [ ] Repayment schedule generation

### Shopping Plan Features
- [ ] Status transition validation
- [ ] Item purchase tracking
- [ ] Move to next plan functionality
- [ ] Out-of-plan item handling

### Saving Goals Features
- [ ] Progress percentage calculation (✅ Already implemented)
- [ ] Remaining amount calculation (✅ Already implemented)
- [ ] Timeline calculation
- [ ] Contribution tracking (✅ Already implemented)

### Tag Features
- [ ] Tag validation:
  - Prevent duplicate tag names per user (✅ Already implemented)
  - Validate tag color format
- [ ] Tag statistics calculation (✅ Already implemented):
  - Total expenses/incomes count
  - Total spent/earned
  - Budgets where tag is used
- [ ] Tag suggestions (for future AI):
  - Suggest tags based on expense/income name
  - Auto-create tags from patterns

---

## Testing & Quality Assurance

### Unit Tests
- [ ] Test user creation/update
- [ ] Test authentication/authorization
- [ ] Test each API endpoint
- [ ] Test business logic functions
- [ ] Test data validation

### Integration Tests
- [ ] Test complete workflows (create budget → add expense → check balance)
- [ ] Test loan repayment flow
- [ ] Test shopping plan lifecycle
- [ ] Test saving goal contributions

### Test Infrastructure
- [ ] Configure pytest
- [ ] Set up test database
- [ ] Create test fixtures
- [ ] Mock external dependencies

---

## Documentation & Deployment

### API Documentation
- [ ] FastAPI auto-generated docs (Swagger UI) - ✅ Already available at `/docs`
- [ ] ReDoc documentation - ✅ Already available at `/redoc`
- [ ] API endpoint descriptions - ✅ Already implemented
- [ ] Request/response examples - ✅ Already implemented
- [ ] Error response examples - ✅ Already implemented

### Code Documentation
- [ ] Docstrings for all functions - ✅ Already implemented
- [ ] Type hints throughout - ✅ Already implemented
- [ ] README.md with setup instructions - ✅ Already created
- [ ] Environment setup guide - ✅ Already created
- [ ] Database migration guide - ✅ Already created

### Error Handling
- [ ] Custom exception classes
- [ ] Global exception handler
- [ ] HTTP status code mapping
- [ ] Error response schemas
- [ ] Validation error formatting

### Security Enhancements
- [ ] CORS configuration - ✅ Already implemented
- [ ] Rate limiting (optional) - See Optional Features above
- [ ] Input sanitization
- [ ] SQL injection prevention (SQLAlchemy ORM) - ✅ Already handled
- [ ] UUID validation - ✅ Already implemented
- [ ] User authorization checks - ✅ Already implemented (users can only access their own data)

### Logging
- [ ] Set up logging configuration
- [ ] Log API requests/responses
- [ ] Log errors with context
- [ ] Log database operations (optional, for debugging)

### Deployment
- [ ] Production settings
- [ ] Environment-specific configs
- [ ] Database connection pooling for production - ✅ Already configured
- [ ] Logging configuration for production

### Containerization
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml (if needed)
- [ ] Multi-stage build optimization

### CI/CD
- [ ] GitHub Actions workflow
- [ ] Automated testing
- [ ] Code quality checks

---

## Database Migrations

- [ ] Create migration: Add AI-related tables (ai_insights, ai_actions) - When AI features are added

---

**Note**: This document is for reference. All core functionality is complete and ready for mobile app integration. These optional features can be added incrementally based on user needs and priorities.

