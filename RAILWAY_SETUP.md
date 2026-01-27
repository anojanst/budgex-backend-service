# Railway Deployment Guide - Using Neon Database

## Quick Setup Steps

### 1. **Deploy from GitHub**
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select `anojanst/budgex-backend-service`
4. Railway will auto-detect the Dockerfile

### 2. **Ignore Railway's PostgreSQL Service**
- Railway may auto-create a `budgex-postgres` service
- **You don't need it** - you're using Neon!
- You can:
  - **Option A**: Delete it (click the service → Settings → Delete)
  - **Option B**: Just ignore it (it won't interfere)

### 3. **Configure Environment Variables**
In your Railway service (the API service, not the postgres one), go to **Variables** tab and add:

#### **Required Variables:**

```env
# Database - Use your Neon database URL
DATABASE_URL=postgresql+asyncpg://neondb_owner:YOUR_PASSWORD@ep-rapid-flower-ahj8bzbe-pooler.c-3.us-east-1.aws.neon.tech/budgex_mobile?sslmode=require

# JWT Configuration
SECRET_KEY=your-generated-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# OTP Configuration
OTP_EXPIRE_MINUTES=10
OTP_LENGTH=6

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ethanojan1@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=ethanojan1@gmail.com
SMTP_TLS=true

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://your-mobile-app-domain.com

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Important Notes:**
- Replace `YOUR_PASSWORD` in `DATABASE_URL` with your actual Neon password
- Generate a secure `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- Update `CORS_ORIGINS` with your actual mobile app domain(s)

### 4. **Set Root Directory (if needed)**
If Railway doesn't detect the service correctly:
- Go to your service → **Settings** → **Root Directory**
- Set it to: `budgex-backend-service` (if deploying from monorepo)
- Or leave blank if the repo root is the backend service

### 4.5. **Check Start Command (IMPORTANT!)**
**CRITICAL**: Railway might have a startCommand override in the UI:
- Go to your service → **Settings** → **Deploy**
- Look for **"Start Command"** field
- **Either:**
  - **Option A**: Set it to `/app/start.sh` (our startup script)
  - **Option B**: **Delete/clear** the startCommand field entirely (let Dockerfile CMD handle it)
- **DO NOT** set it to `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (this won't expand $PORT)

### 5. **Deploy**
- Railway will automatically build and deploy
- Watch the **Deployments** tab for build logs
- Wait for status: **"Active"**

### 6. **Run Migrations**
After first deployment:

**Option A: Via Railway Shell**
1. Go to your service → **Shell** tab
2. Run:
   ```bash
   alembic upgrade head
   ```

**Option B: Via Railway CLI**
```bash
railway run alembic upgrade head
```

### 7. **Verify Deployment**
1. Get your Railway URL (e.g., `https://your-app.up.railway.app`)
2. Test endpoints:
   ```bash
   curl https://your-app.up.railway.app/health
   curl https://your-app.up.railway.app/health/db
   ```
3. Check API docs: `https://your-app.up.railway.app/docs`

### 8. **Custom Domain (Optional)**
- Go to **Settings** → **Networking**
- Add your custom domain
- Railway provides free SSL automatically

---

## Troubleshooting

### Database Connection Issues
- **Verify DATABASE_URL format**: Must use `postgresql+asyncpg://` (not `postgresql://`)
- **Check Neon connection**: Ensure Neon database is accessible from Railway's IPs
- **SSL mode**: Neon requires `sslmode=require`

### Build Failures
- Check **Deployments** → **Logs** for errors
- Ensure `Dockerfile` is in the root directory
- Verify all dependencies in `requirements.txt`

### Migration Errors
- Ensure `DATABASE_URL` is set correctly
- Check Neon database is accessible
- Run migrations via Railway Shell

---

## Railway vs Neon Database

**Railway PostgreSQL (`budgex-postgres`):**
- ❌ Not needed - you're using Neon
- Can be deleted safely
- Won't interfere if left alone

**Neon Database:**
- ✅ Your production database
- Set via `DATABASE_URL` environment variable
- Already configured and working locally

---

## Cost Comparison

- **Railway**: $5/month credit (free tier)
- **Neon**: Free tier available (generous limits)
- **Total**: Can run for free on both platforms!

---

## Next Steps After Deployment

1. ✅ API is live on Railway
2. ✅ Connected to Neon database
3. ✅ Migrations applied
4. 🔄 Update mobile app to use Railway URL
5. 🔄 Set up monitoring/alerts (optional)

