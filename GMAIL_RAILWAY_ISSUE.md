# Gmail SMTP Timeout Issue in Railway

## Problem

Gmail SMTP is timing out on Railway even with:
- ✅ Correct App Password
- ✅ Port 465 (SSL) or Port 587 (STARTTLS)
- ✅ 2FA enabled
- ✅ Correct credentials

**Error**: `Timed out connecting to smtp.gmail.com on port 465/587`

## Root Cause

This is **NOT a configuration issue**. The problem is:

1. **Gmail blocks cloud provider IPs**: Railway's IP addresses are often blocked by Gmail's security policies
2. **Network restrictions**: Railway may have firewall rules preventing outbound SMTP connections
3. **IP reputation**: Gmail's anti-spam systems flag cloud provider IPs as suspicious

## Solutions

### Option 1: Use SendGrid (Recommended - 5 minutes setup)

**Free tier**: 100 emails/day

1. Sign up at https://sendgrid.com
2. Verify your sender email
3. Create API key
4. Update Railway variables:

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key-here
SMTP_FROM_EMAIL=your-verified-email@yourdomain.com
SMTP_TLS=true
```

**Benefits**:
- ✅ Works reliably in Railway
- ✅ Better deliverability
- ✅ Free tier sufficient for development
- ✅ No IP blocking issues

### Option 2: Use Mailgun (Alternative)

**Free tier**: 5,000 emails/month

1. Sign up at https://mailgun.com
2. Verify your domain
3. Get SMTP credentials
4. Update Railway variables:

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_TLS=true
```

### Option 3: Use Gmail API (Complex)

Instead of SMTP, use Gmail API:
- Requires OAuth2 setup
- More complex implementation
- Still may have rate limits

**Not recommended** - Use SendGrid instead.

### Option 4: Use Railway's Email Service (If Available)

Check if Railway offers an email service or SMTP relay.

## Why Gmail Doesn't Work

1. **Security policies**: Gmail blocks many cloud provider IPs to prevent spam
2. **Rate limiting**: Strict limits on SMTP connections from unknown IPs
3. **IP reputation**: Railway's shared IPs may be flagged
4. **Network restrictions**: Railway may block outbound SMTP ports

## Quick Fix: Switch to SendGrid

**Time**: 5 minutes
**Cost**: Free (100 emails/day)

1. Go to https://sendgrid.com → Sign up (free)
2. Go to Settings → API Keys → Create API Key
3. Copy the API key
4. In Railway → Variables:
   ```env
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=paste-your-api-key-here
   SMTP_FROM_EMAIL=your-email@gmail.com  # Or your verified domain
   SMTP_TLS=true
   ```
5. Redeploy - Railway will automatically redeploy

**That's it!** SendGrid works immediately in Railway.

## Testing After Switch

```bash
curl -X POST https://your-app.up.railway.app/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check Railway logs - you should see: `OTP email sent successfully`

## Recommendation

**For production**: Use SendGrid or Mailgun
**For development**: Use SendGrid (free tier is sufficient)

Gmail SMTP is not reliable for cloud deployments. Use a dedicated email service instead.

