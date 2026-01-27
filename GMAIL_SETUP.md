# Gmail SMTP Setup for Railway

## Quick Setup Steps

### Step 1: Enable 2-Factor Authentication on Gmail

1. Go to https://myaccount.google.com/security
2. Under "Signing in to Google", click **"2-Step Verification"**
3. Follow the prompts to enable 2FA (you'll need your phone)

### Step 2: Generate App Password

1. Go to https://myaccount.google.com/apppasswords
   - If you don't see this link, make sure 2FA is enabled first
2. Under "Select app", choose **"Mail"**
3. Under "Select device", choose **"Other (Custom name)"**
4. Enter: `BudgeX API` (or any name you prefer)
5. Click **"Generate"**
6. **Copy the 16-character password** (it looks like: `xxxx xxxx xxxx xxxx`)
   - ⚠️ **Important**: You can only see this password once! Save it immediately.

### Step 3: Update Railway Environment Variables

In your Railway project → Your API service → **Variables** tab:

#### Option A: Port 587 (STARTTLS) - Try this first
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The App Password (spaces optional)
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TLS=true
```

#### Option B: Port 465 (SSL) - If 587 times out
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The App Password (spaces optional)
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_TLS=true
```

### Step 4: Redeploy

Railway will automatically redeploy when you save the variables. Check the logs to verify:

```bash
# In Railway logs, you should see:
# "OTP email sent successfully to {email}"
```

## Troubleshooting

### Still Getting Timeout?

1. **Try Port 465**: Switch from port 587 to 465 (see Option B above)
2. **Check App Password**: Make sure you're using the App Password, not your regular Gmail password
3. **Verify 2FA**: Ensure 2-Step Verification is enabled
4. **Check Railway Logs**: Look for specific error messages

### "Invalid credentials" Error?

- Make sure you're using the **App Password** (16 characters), not your regular password
- Remove any spaces from the App Password if you copied it with spaces
- Regenerate the App Password if needed

### "Less secure app access" Error?

- Gmail no longer supports "less secure apps"
- You **must** use App Passwords with 2FA enabled
- This is the only way to use Gmail SMTP now

## Testing

After setup, test the endpoint:

```bash
curl -X POST https://your-app.up.railway.app/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check Railway logs to see if the email was sent successfully.

## Important Notes

- ⚠️ **App Passwords are required** - Regular Gmail passwords won't work
- ⚠️ **2FA must be enabled** - You can't generate App Passwords without it
- 🔒 **Keep App Password secret** - Treat it like a regular password
- 📧 **Port 465 is more reliable** - If 587 times out, use 465 with SSL

## Alternative: Use SendGrid (Recommended for Production)

For production deployments, consider using SendGrid instead:
- More reliable in cloud environments
- Better deliverability
- Free tier: 100 emails/day
- See `EMAIL_TROUBLESHOOTING.md` for setup instructions

