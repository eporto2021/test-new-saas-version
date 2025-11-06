# MailerSend Email Configuration

This document explains how to set up MailerSend as your email provider for production.

## Prerequisites

1. Create a MailerSend account at [https://www.mailersend.com/](https://www.mailersend.com/)
2. Get your API key from the MailerSend dashboard

## Environment Variables

Set the following environment variables in your Fly.io app:

### Required Variables

```bash
# MailerSend API Key (get this from your MailerSend dashboard)
MAILERSEND_API_KEY=your_mailersend_api_key_here

# Email backend (already configured in production settings)
EMAIL_BACKEND=anymail.backends.mailersend.EmailBackend

# Default from email (should be a verified domain in MailerSend)
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=noreply@yourdomain.com
```

### Optional Variables

```bash
# MailerSend API URL (defaults to https://api.mailersend.com/v1)
MAILERSEND_API_URL=https://api.mailersend.com/v1
```

## Setting Environment Variables in Fly.io

### Method 1: Using Fly CLI

```bash
# Set the MailerSend API key
fly secrets set MAILERSEND_API_KEY=your_actual_api_key_here --app test-blue-smoke-97

# Set the from email (use your verified domain)
fly secrets set DEFAULT_FROM_EMAIL=noreply@yourdomain.com --app test-blue-smoke-97
fly secrets set SERVER_EMAIL=noreply@yourdomain.com --app test-blue-smoke-97
```

### Method 2: Using Fly Dashboard

1. Go to your app dashboard: https://fly.io/apps/test-blue-smoke-97
2. Click on "Secrets" in the left sidebar
3. Add the following secrets:
   - `MAILERSEND_API_KEY`: Your MailerSend API key
   - `DEFAULT_FROM_EMAIL`: Your verified sender email
   - `SERVER_EMAIL`: Your verified sender email

## Domain Verification

Before sending emails, you need to verify your domain in MailerSend:

1. Log into your MailerSend dashboard
2. Go to "Domains" section
3. Add your domain (e.g., `yourdomain.com`)
4. Add the required DNS records to verify domain ownership
5. Wait for verification to complete

## Testing Email Configuration

After setting up the environment variables, test the email configuration:

```bash
# SSH into your Fly app
fly ssh console --app test-blue-smoke-97

# Run the test email command
python manage.py send_test_email your-email@example.com
```

## Troubleshooting

### Common Issues

1. **"Invalid API key"**: Check that your `MAILERSEND_API_KEY` is correct
2. **"Domain not verified"**: Ensure your sending domain is verified in MailerSend
3. **"From address not authorized"**: Use a verified email address for `DEFAULT_FROM_EMAIL`

### Checking Logs

```bash
# Check recent logs for email-related errors
fly logs --app test-blue-smoke-97 | grep -i "mail\|email\|anymail"
```

### Django Debug

You can temporarily enable debug logging for emails by setting:

```bash
fly secrets set DJANGO_LOG_LEVEL=DEBUG --app test-blue-smoke-97
```

## Email Templates

The app uses Django's built-in email templates for:
- Account confirmation emails
- Password reset emails
- Admin notifications
- Subscription request notifications

These will automatically use your MailerSend configuration once set up.

## Production Checklist

- [ ] MailerSend account created
- [ ] API key obtained
- [ ] Domain verified in MailerSend
- [ ] Environment variables set in Fly.io
- [ ] Test email sent successfully
- [ ] Account creation emails working
- [ ] Password reset emails working
