# Email & SMS Setup Guide

## Overview

The forgot password feature now supports sending verification codes via email and SMS. This guide explains how to configure both services.

---

## Email Configuration (SMTP)

### Option 1: Gmail SMTP (Recommended for Testing)

1. **Enable App Password in Gmail:**
   - Go to your Google Account settings
   - Security → 2-Step Verification (enable if not already)
   - App passwords → Generate app password
   - Copy the 16-character password

2. **Add to `.env` file:**
   ```env
   # Email Configuration (Gmail)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM_EMAIL=your-email@gmail.com
   SMTP_FROM_NAME=AyudaBesh
   ```

### Option 2: Other SMTP Servers

For other email providers, update the SMTP settings:

**Outlook/Hotmail:**
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

**Yahoo:**
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

**Custom SMTP:**
```env
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=AyudaBesh
```

---

## SMS Configuration (Twilio)

### Setup Twilio Account

1. **Create Twilio Account:**
   - Go to https://www.twilio.com
   - Sign up for a free account
   - Get your Account SID and Auth Token from the dashboard
   - Get a phone number (free trial includes a number)

2. **Install Twilio:**
   ```bash
   pip install twilio
   ```

3. **Add to `.env` file:**
   ```env
   # SMS Configuration (Twilio)
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### Alternative SMS Services

You can modify `lib/email_service.py` to use other SMS services:
- AWS SNS
- Nexmo/Vonage
- MessageBird
- Custom SMS gateway

---

## Testing

### Test Email Sending

1. Configure SMTP settings in `.env`
2. Restart your Flask server
3. Go to `/forgot-password`
4. Enter an email address
5. Check the email inbox for verification code

### Test SMS Sending

1. Configure Twilio settings in `.env`
2. Install Twilio: `pip install twilio`
3. Restart your Flask server
4. Go to `/forgot-password`
5. Enter a phone number (with country code, e.g., +1234567890)
6. Check your phone for SMS

---

## Fallback Behavior

If email/SMS is not configured:
- Verification code is printed to console
- Code is returned in API response (for development)
- User can still complete password reset

This allows development/testing without email/SMS setup.

---

## Environment Variables Summary

Add these to your `.env` file:

```env
# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=AyudaBesh

# SMS (Twilio) - Optional
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## Troubleshooting

### Email Not Sending

1. **Check SMTP credentials** - Verify username and password are correct
2. **Check firewall** - Port 587 must be open
3. **Gmail App Password** - Make sure you're using an app password, not your regular password
4. **Check console** - Look for error messages in server logs

### SMS Not Sending

1. **Check Twilio credentials** - Verify Account SID and Auth Token
2. **Check phone number format** - Must include country code (e.g., +1 for US)
3. **Check Twilio balance** - Free trial has limits
4. **Install Twilio** - Run `pip install twilio`

### Both Not Working

- Check `.env` file exists and variables are set correctly
- Restart Flask server after changing `.env`
- Check console output for error messages
- Verification code will still be in API response for development

---

## Security Notes

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use app passwords** - Don't use your main email password
3. **Rotate credentials** - Change passwords/tokens regularly
4. **Production** - Use dedicated email/SMS services in production
5. **Rate limiting** - Consider adding rate limiting to prevent abuse

---

## Production Recommendations

For production, consider:
- **Email**: SendGrid, AWS SES, Mailgun
- **SMS**: Twilio, AWS SNS, MessageBird
- **Rate limiting**: Limit password reset requests per user/IP
- **Monitoring**: Log all email/SMS sending attempts
- **Templates**: Use professional email templates
