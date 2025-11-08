# Welcome Email Setup

This document explains how the welcome email system works and how to configure it.

## Overview

When a new user signs up, the system automatically sends them a welcome email. This happens through Django signals that trigger when a user account is created.

## How It Works

### 1. User Signup Flow

```
User Signs Up
    ↓
Account Created (CustomUser object saved)
    ↓
Signal Triggered: send_welcome_email()
    ↓
Welcome Email Sent
    ↓
(Optional) Email Confirmation Sent
    ↓
User Receives Emails
```

### 2. Signal Implementation

Located in `apps/users/signals.py`:

```python
@receiver(post_save, sender=CustomUser)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send a welcome email to new users after they sign up.
    """
    if created and instance.email:
        # Send personalized welcome email
        send_mail(
            subject=f"Welcome to {project_name}!",
            message=welcome_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,
        )
```

**When it triggers:**
- Only on user creation (`created=True`)
- Only if user has an email address
- Runs automatically, no manual intervention needed

## Configuration

### Email Backend

**Development:**
```python
# test/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Emails print to console for testing.

**Production:**
```python
# test/settings_production.py
EMAIL_BACKEND = "anymail.backends.mailersend.EmailBackend"
ANYMAIL = {
    "MAILERSEND_API_TOKEN": env("MAILERSEND_API_KEY"),
}
```

### Required Settings

1. **MAILERSEND_API_KEY** (Production)
   ```bash
   fly secrets set MAILERSEND_API_KEY=your_key_here --app test-blue-smoke-97
   ```

2. **DEFAULT_FROM_EMAIL** (All environments)
   ```python
   # test/settings.py
   DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"
   ```

3. **PROJECT_METADATA** (Customize branding)
   ```python
   # test/settings.py
   PROJECT_METADATA = {
       "NAME": "Eporto",
       "CONTACT_EMAIL": "maxdavenport96@gmail.com",
       # ... other metadata
   }
   ```

## Email Verification

### Settings

```python
# test/settings.py
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # Options: "none", "optional", "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
```

**Options:**
- `"none"` - No email verification required
- `"optional"` - Send verification email, but users can log in without verifying
- `"mandatory"` - Users must verify email before logging in

### Current Configuration

✅ **Email verification is enabled** (`mandatory`)
✅ **Users receive:**
1. Welcome email (custom)
2. Email confirmation link (django-allauth)

## Customizing the Welcome Email

### 1. Edit the Message

File: `apps/users/signals.py`

```python
message = f"""
Hi {instance.first_name or 'there'},

Welcome to {project_name}! We're excited to have you on board.

Your account has been created successfully. You can now log in and start using our services.

If you have any questions or need assistance, feel free to reach out to our support team at {settings.PROJECT_METADATA.get('CONTACT_EMAIL', 'support@eporto.com')}.

Best regards,
The {project_name} Team
""".strip()
```

### 2. Use HTML Templates (Advanced)

For rich HTML emails, replace `send_mail()` with `send_html_mail()`:

```python
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

# Create welcome email template at: templates/emails/welcome.html
html_content = render_to_string('emails/welcome.html', {
    'user': instance,
    'project_name': project_name,
})

email = EmailMultiAlternatives(
    subject=f"Welcome to {project_name}!",
    body=message,  # Plain text fallback
    from_email=settings.DEFAULT_FROM_EMAIL,
    to=[instance.email]
)
email.attach_alternative(html_content, "text/html")
email.send()
```

### 3. Add More Information

You can include:
- Links to getting started guides
- Feature highlights
- Special offers
- Onboarding steps
- Social media links

## Testing

### Local Testing

1. **Start Django development server:**
   ```bash
   docker compose up
   ```

2. **Sign up a new user:**
   - Navigate to `/accounts/signup/`
   - Fill out the form
   - Submit

3. **Check console output:**
   The welcome email will print to the console:
   ```
   Content-Type: text/plain; charset="utf-8"
   Subject: Welcome to Eporto!
   From: noreply@eporto.com
   To: newuser@example.com
   
   Hi John,
   
   Welcome to Eporto! ...
   ```

### Production Testing

1. **Check MailerSend API Key:**
   ```bash
   fly secrets list --app test-blue-smoke-97 | grep MAILERSEND
   ```

2. **Sign up a test user**

3. **Check logs:**
   ```bash
   fly logs --app test-blue-smoke-97 | grep "Welcome email"
   ```

4. **Check user's inbox:**
   - Look for email from your domain
   - Check spam folder if not found

## Troubleshooting

### Emails Not Sending

**Issue:** Welcome emails not being sent

**Solutions:**

1. **Check logs:**
   ```bash
   fly logs --app test-blue-smoke-97 | grep "email\|Welcome"
   ```

2. **Verify MailerSend API Key:**
   ```bash
   fly ssh console --app test-blue-smoke-97
   source /code/.venv/bin/activate
   python manage.py shell
   ```
   ```python
   from django.conf import settings
   print(settings.MAILERSEND_API_KEY)
   ```

3. **Check email backend:**
   ```python
   print(settings.EMAIL_BACKEND)
   # Should be: anymail.backends.mailersend.EmailBackend
   ```

4. **Test email manually:**
   ```bash
   python manage.py test_email your@email.com
   ```

### Email Goes to Spam

**Solutions:**
- Configure SPF records for your domain
- Configure DKIM in MailerSend
- Add DMARC policy
- Verify domain in MailerSend
- Use a verified sender email

### Signal Not Triggering

**Check that signals are connected:**

File: `apps/users/apps.py`

```python
class UsersConfig(AppConfig):
    name = 'apps.users'
    
    def ready(self):
        import apps.users.signals  # Import signals
```

## Additional Features

### Send Email to Admin on New Signup

Add another signal:

```python
@receiver(post_save, sender=CustomUser)
def notify_admin_new_user(sender, instance, created, **kwargs):
    """Notify admin when new user signs up."""
    if created:
        send_mail(
            subject=f"New User Signup: {instance.email}",
            message=f"New user {instance.get_display_name()} has signed up.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email for name, email in settings.ADMINS],
            fail_silently=True,
        )
```

### Welcome Email with Onboarding Steps

```python
message = f"""
Hi {instance.first_name or 'there'},

Welcome to {project_name}! Here's how to get started:

1. Complete your profile
2. Subscribe to a service
3. Upload your first file
4. Explore our features

Get started now: {settings.PROJECT_METADATA.get('URL')}

Need help? Contact us at {contact_email}

Best regards,
The {project_name} Team
"""
```

## Related Files

- `apps/users/signals.py` - Signal implementations
- `apps/users/adapter.py` - Email sending adapter
- `test/settings.py` - Email configuration
- `test/settings_production.py` - Production email backend
- `templates/account/email/` - Django-allauth email templates

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAILERSEND_API_KEY` | Production | None | MailerSend API key |
| `DEFAULT_FROM_EMAIL` | All | noreply@localhost | Sender email address |
| `ACCOUNT_EMAIL_VERIFICATION` | All | mandatory | Email verification mode |

## References

- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Django Signals Documentation](https://docs.djangoproject.com/en/stable/topics/signals/)
- [MailerSend Documentation](https://www.mailersend.com/help/getting-started)
- [Django-allauth Email Configuration](https://django-allauth.readthedocs.io/en/latest/configuration.html)

---

**Last Updated:** November 7, 2025

