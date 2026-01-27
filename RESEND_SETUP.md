# Resend Email Setup Guide

## Quick Setup (2 minutes)

### Step 1: Get Resend API Key

1. Sign up at https://resend.com (free tier: 3,000 emails/month)
2. Go to **API Keys** → **Create API Key**
3. Copy your API key (starts with `re_`)

### Step 2: Update Railway Environment Variables

In your Railway project → Your API service → **Variables** tab:

```env
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev  # Default for testing
```

**For testing**: Use `onboarding@resend.dev` (works immediately)

**For production**: 
1. Verify your domain in Resend dashboard
2. Update `RESEND_FROM_EMAIL` to `noreply@yourdomain.com` or similar

### Step 3: Redeploy

Railway will automatically redeploy when you save the variables.

## Testing

After setup, test the endpoint:

```bash
curl -X POST https://your-app.up.railway.app/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check Railway logs - you should see: `OTP email sent successfully via Resend`

## Domain Verification (For Production)

1. Go to https://resend.com/domains
2. Click **Add Domain**
3. Add your domain (e.g., `yourdomain.com`)
4. Add the DNS records Resend provides to your domain's DNS
5. Wait for verification (usually a few minutes)
6. Update `RESEND_FROM_EMAIL` to use your verified domain

## Benefits of Resend

- ✅ **Works reliably** in Railway/cloud platforms
- ✅ **No SMTP issues** - uses modern REST API
- ✅ **Fast delivery** - optimized for transactional emails
- ✅ **Free tier**: 3,000 emails/month
- ✅ **Great developer experience** - simple API
- ✅ **No IP blocking** - unlike Gmail SMTP

## Environment Variables

```env
# Required
RESEND_API_KEY=re_your_api_key_here

# Optional (defaults to onboarding@resend.dev for testing)
RESEND_FROM_EMAIL=onboarding@resend.dev
```

## Troubleshooting

### "Unauthorized" Error
- Check `RESEND_API_KEY` is set correctly
- Verify API key is valid in Resend dashboard
- Make sure there are no extra spaces in the API key

### "Domain not verified" Error
- For testing: Use `onboarding@resend.dev`
- For production: Verify your domain in Resend dashboard
- Update `RESEND_FROM_EMAIL` to use verified domain

### Email not received
- Check spam folder
- Verify recipient email is correct
- Check Resend dashboard → Logs for delivery status

## Migration from Gmail SMTP

If you were using Gmail SMTP before:

1. Remove these variables (no longer needed):
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
   - `SMTP_FROM_EMAIL`
   - `SMTP_TLS`

2. Add these variables:
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL` (optional, defaults to onboarding@resend.dev)

3. Redeploy - that's it!

## Cost

- **Free tier**: 3,000 emails/month
- **Paid**: $20/month for 50,000 emails
- Perfect for most applications!

