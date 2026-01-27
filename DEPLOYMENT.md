# BudgeX Backend Deployment Guide

This guide covers deploying the BudgeX FastAPI backend to various cloud platforms.

## Quick Start - Recommended Platforms

### 🚀 Railway (Recommended - Easiest)

**Why Railway?**
- Zero-config deployment
- Automatic HTTPS
- Built-in PostgreSQL database
- Free tier available
- GitHub integration

**Steps:**

1. **Sign up at [Railway.app](https://railway.app)**

2. **Create a new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository
   - Select the `budgex-backend-service` directory

3. **Add PostgreSQL database:**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway automatically provides `DATABASE_URL` environment variable

4. **Configure environment variables:**
   - Go to project settings → Variables
   - Add the following (see `.env.example`):
     ```
     SECRET_KEY=<generate-a-secure-random-key>
     ALGORITHM=HS256
     ACCESS_TOKEN_EXPIRE_DAYS=30
     OTP_EXPIRE_MINUTES=10
     OTP_LENGTH=6
     SMTP_HOST=<your-smtp-host>
     SMTP_PORT=587
     SMTP_USER=<your-smtp-user>
     SMTP_PASSWORD=<your-smtp-password>
     SMTP_FROM_EMAIL=<your-email>
     SMTP_TLS=true
     CORS_ORIGINS=<your-mobile-app-urls>
     ENVIRONMENT=production
     DEBUG=false
     ```

5. **Deploy:**
   - Railway automatically detects Dockerfile and deploys
   - Or set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. **Run migrations:**
   - Open Railway CLI or use web terminal
   - Run: `alembic upgrade head`

7. **Access your API:**
   - Railway provides a public URL (e.g., `https://your-app.railway.app`)
   - API docs: `https://your-app.railway.app/docs`

---

### 🌐 Render

**Why Render?**
- Free tier with PostgreSQL
- Automatic SSL
- GitHub auto-deploy
- Simple configuration

**Steps:**

1. **Sign up at [Render.com](https://render.com)**

2. **Create PostgreSQL database:**
   - New → PostgreSQL
   - Copy the "Internal Database URL"

3. **Create Web Service:**
   - New → Web Service
   - Connect GitHub repository
   - Select `budgex-backend-service` directory
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables:**
   - Add all variables from `.env.example`
   - Use the PostgreSQL URL from step 2 for `DATABASE_URL`

5. **Deploy:**
   - Render automatically deploys on git push
   - Run migrations via shell: `alembic upgrade head`

---

### ✈️ Fly.io

**Why Fly.io?**
- Global edge deployment
- Free tier
- Great for low latency

**Steps:**

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create app:**
   ```bash
   fly launch
   ```
   - Follow prompts
   - Don't deploy yet

4. **Create PostgreSQL database:**
   ```bash
   fly postgres create --name budgex-db
   fly postgres attach budgex-db -a budgex-backend
   ```

5. **Set secrets:**
   ```bash
   fly secrets set SECRET_KEY=<your-secret-key>
   fly secrets set SMTP_HOST=<your-smtp-host>
   # ... add all other secrets
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

7. **Run migrations:**
   ```bash
   fly ssh console -C "alembic upgrade head"
   ```

---

## Docker Deployment

### Local Development with Docker Compose

```bash
# Copy .env.example to .env and fill in values
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Build and Run Docker Image

```bash
# Build image
docker build -t budgex-backend .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  budgex-backend
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT secret key (generate random) | `openssl rand -hex 32` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_USER` | SMTP username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP password | `your-app-password` |
| `SMTP_FROM_EMAIL` | Sender email address | `noreply@budgex.com` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `30` | Token expiration days |
| `OTP_EXPIRE_MINUTES` | `10` | OTP expiration minutes |
| `OTP_LENGTH` | `6` | OTP code length |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_TLS` | `true` | Enable TLS |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `ENVIRONMENT` | `development` | Environment name |
| `DEBUG` | `false` | Debug mode |

---

## Pre-Deployment Checklist

- [ ] Generate secure `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] Set up PostgreSQL database (or use platform's managed database)

- [ ] Configure SMTP settings (Gmail, SendGrid, AWS SES, etc.)

- [ ] Set `CORS_ORIGINS` to your mobile app URLs

- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`

- [ ] Run database migrations:
  ```bash
  alembic upgrade head
  ```

- [ ] Test health endpoint:
  ```bash
  curl https://your-api-url/health
  ```

- [ ] Test database health:
  ```bash
  curl https://your-api-url/health/db
  ```

---

## CI/CD with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

- Lints code on push/PR
- Runs tests (when test files are added)
- Builds Docker image
- Validates code formatting

To enable:
1. Push code to GitHub
2. GitHub Actions runs automatically
3. Check Actions tab for status

---

## Monitoring & Logs

### Railway
- View logs in Railway dashboard
- Set up monitoring alerts

### Render
- View logs in Render dashboard
- Set up health checks

### Fly.io
```bash
# View logs
fly logs

# Monitor
fly status
```

---

## Database Migrations

Always run migrations after deployment:

```bash
# Via platform CLI/terminal
alembic upgrade head

# Or via Docker
docker-compose exec api alembic upgrade head
```

---

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql+asyncpg://...`
- Check database is accessible from deployment platform
- Verify SSL settings if required

### SMTP Issues
- Use app-specific password for Gmail
- Check SMTP port (587 for TLS, 465 for SSL)
- Verify firewall allows SMTP connections

### CORS Issues
- Set `CORS_ORIGINS` to exact mobile app URLs
- Include protocol (`https://`) and port if needed

### Migration Errors
- Ensure database is empty or migrations are sequential
- Check Alembic version history: `alembic history`

---

## Security Best Practices

1. **Never commit `.env` files**
2. **Use strong `SECRET_KEY`** (32+ characters, random)
3. **Enable HTTPS** (automatic on Railway/Render/Fly.io)
4. **Set `DEBUG=false`** in production
5. **Limit `CORS_ORIGINS`** to specific domains
6. **Use managed databases** with automatic backups
7. **Rotate secrets** periodically
8. **Monitor logs** for suspicious activity

---

## Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Railway** | $5/month credit | Pay-as-you-go | Easiest setup |
| **Render** | Free (with limits) | $7+/month | Simple deployments |
| **Fly.io** | Free (3 VMs) | Pay-as-you-go | Global edge |
| **DigitalOcean** | No | $12+/month | Full control |
| **AWS/GCP** | Free tier | Pay-as-you-go | Enterprise scale |

---

## Recommended Setup for Production

1. **Use Railway or Render** for simplicity
2. **Use managed PostgreSQL** (platform-provided)
3. **Set up email service** (SendGrid, AWS SES, or Mailgun)
4. **Enable monitoring** (platform dashboards)
5. **Set up backups** (automatic with managed databases)
6. **Configure custom domain** (optional)

---

## Support

For deployment issues:
1. Check platform documentation
2. Review logs in platform dashboard
3. Verify environment variables
4. Test locally with Docker Compose first

