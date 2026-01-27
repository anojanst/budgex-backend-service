# .env File Format Guide

## Important: CORS_ORIGINS Format

The `CORS_ORIGINS` variable should be a **comma-separated string**, NOT a JSON array.

### ✅ Correct Format:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com
```

### ❌ Incorrect Format (will cause parsing errors):
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## Complete .env Example

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/budgex_mobile_db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30
REFRESH_TOKEN_EXPIRE_DAYS=90

# OTP Configuration
OTP_EXPIRE_MINUTES=10
OTP_LENGTH=6
OTP_MAX_ATTEMPTS=3

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@budgex.com
SMTP_TLS=true

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379/0
USE_REDIS_FOR_OTP=false

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development
DEBUG=true

# Logging
LOG_LEVEL=INFO
```

## Notes

1. **No quotes needed** for string values (unless the value itself contains spaces or special characters)
2. **No JSON arrays** - use comma-separated strings
3. **Boolean values** should be lowercase: `true` or `false`
4. **Numbers** don't need quotes

