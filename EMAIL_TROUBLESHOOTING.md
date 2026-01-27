# Email Troubleshooting Guide

## Common Issues in Railway/Cloud Deployments

### Issue: "Timed out connecting to smtp.gmail.com"

This is a common problem when using Gmail SMTP from cloud platforms like Railway.

### Solutions

#### Option 1: Use Gmail App Password (Required for Gmail)

Gmail requires **App Passwords** (not regular passwords) for third-party apps:

1. **Enable 2-Factor Authentication** on your Gmail account:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "BudgeX API" as the name
   - Copy the 16-character password

3. **Update Railway Environment Variables**:
   ```env
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # Use the App Password (spaces optional)
   ```

#### Option 2: Try Port 465 with SSL

Port 587 (STARTTLS) may be blocked. Try port 465 (SSL):

**In Railway Variables:**
```env
SMTP_PORT=465
SMTP_TLS=true
```

The code automatically detects port 465 and uses SSL instead of STARTTLS.

#### Option 3: Use a Production Email Service (Recommended)

For production, consider using dedicated email services:

**SendGrid (Free tier: 100 emails/day)**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=your-verified-sender@yourdomain.com
SMTP_TLS=true
```

**Mailgun (Free tier: 5,000 emails/month)**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_TLS=true
```

**AWS SES (Free tier: 62,000 emails/month)**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-aws-smtp-username
SMTP_PASSWORD=your-aws-smtp-password
SMTP_FROM_EMAIL=verified-email@yourdomain.com
SMTP_TLS=true
```

### Quick Fix Checklist

- [ ] Using Gmail App Password (not regular password)
- [ ] 2FA enabled on Gmail account
- [ ] Tried port 465 instead of 587
- [ ] Verified SMTP credentials in Railway variables
- [ ] Checked Railway logs for specific error messages
- [ ] Considered switching to SendGrid/Mailgun for production

### Testing Email Configuration

After updating Railway variables, test the endpoint:

```bash
curl -X POST https://your-app.up.railway.app/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check Railway logs for detailed error messages.

### Why Gmail Fails in Cloud Deployments

1. **IP Reputation**: Railway's IPs may not be trusted by Gmail
2. **Rate Limiting**: Gmail has strict rate limits for SMTP
3. **Security Policies**: Gmail blocks many cloud provider IPs
4. **Port Restrictions**: Some cloud providers block port 587

**Recommendation**: Use SendGrid or Mailgun for production deployments.

