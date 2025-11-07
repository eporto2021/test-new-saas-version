"""
Management command to test email sending configuration.

This command sends a test email to verify that your email backend is configured correctly.
It's especially useful for testing production email settings (MailerSend).

Usage:
    # Test with default recipient (from DEFAULT_FROM_EMAIL)
    python manage.py test_email

    # Test with specific recipient
    python manage.py test_email --to recipient@example.com

    # Test in production via Fly.io
    fly ssh console -C "python manage.py test_email --to your@email.com" -a test-blue-smoke-97
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Send a test email to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='Email address to send test email to',
            default=None,
        )

    def handle(self, *args, **options):
        recipient = options.get('to') or getattr(settings, 'DEFAULT_FROM_EMAIL', 'test@example.com')
        
        # Show current email backend configuration
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📧 Email Configuration Test'))
        self.stdout.write('=' * 60)
        
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
        self.stdout.write(f'\n📮 Email Backend: {email_backend}')
        
        # Check if in production mode
        stripe_live_mode = getattr(settings, 'STRIPE_LIVE_MODE', False)
        environment = 'PRODUCTION (Live)' if stripe_live_mode else 'DEVELOPMENT (Test)'
        self.stdout.write(f'🌍 Environment: {environment}')
        
        # Show MailerSend configuration if applicable
        if 'mailersend' in email_backend.lower():
            self.stdout.write(f'✅ Using MailerSend')
            mailersend_key = getattr(settings, 'MAILERSEND_API_KEY', 'Not set')
            if mailersend_key and mailersend_key != 'Not set':
                masked_key = mailersend_key[:8] + '...' + mailersend_key[-4:] if len(mailersend_key) > 12 else '***'
                self.stdout.write(f'🔑 API Key: {masked_key}')
            else:
                self.stdout.write(self.style.ERROR('❌ MailerSend API Key not configured'))
        elif 'console' in email_backend.lower():
            self.stdout.write(self.style.WARNING('⚠️  Using Console Backend (emails will be printed to logs, not sent)'))
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        self.stdout.write(f'📤 From: {from_email}')
        self.stdout.write(f'📥 To: {recipient}')
        
        # Prepare test email
        subject = f'Test Email from {settings.PROJECT_METADATA.get("NAME", "Your App")} - {environment}'
        message = f"""
This is a test email to verify your email configuration.

Configuration Details:
- Environment: {environment}
- Email Backend: {email_backend}
- From Address: {from_email}
- To Address: {recipient}

If you received this email, your email configuration is working correctly! ✅

---
Sent via Django management command: python manage.py test_email
"""
        
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write('Sending test email...')
        self.stdout.write('-' * 60 + '\n')
        
        try:
            # Send the email
            result = send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(self.style.SUCCESS('\n✅ Email sent successfully!'))
                
                if 'console' in email_backend.lower():
                    self.stdout.write(self.style.WARNING('\n⚠️  Console backend detected:'))
                    self.stdout.write('   Email was printed above in the logs (not actually sent).')
                    self.stdout.write('   To actually send emails, configure MailerSend in production.')
                else:
                    self.stdout.write(f'\n📬 Check {recipient} inbox (and spam folder)')
                    self.stdout.write('   If you don\'t see the email:')
                    self.stdout.write('   1. Check your spam/junk folder')
                    self.stdout.write('   2. Verify your MailerSend domain is verified')
                    self.stdout.write('   3. Check MailerSend dashboard for delivery logs')
                
                self.stdout.write('\n' + '=' * 60 + '\n')
                return
            else:
                self.stdout.write(self.style.ERROR('❌ Email sending failed (no exception but result != 1)'))
                sys.exit(1)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error sending email: {str(e)}'))
            self.stdout.write(self.style.ERROR(f'Exception type: {type(e).__name__}'))
            
            # Provide troubleshooting tips
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.ERROR('Troubleshooting Tips:'))
            self.stdout.write('=' * 60)
            
            if 'mailersend' in email_backend.lower():
                self.stdout.write('1. Verify MAILERSEND_API_KEY is set correctly')
                self.stdout.write('2. Check that your sending domain is verified in MailerSend')
                self.stdout.write('3. Ensure DEFAULT_FROM_EMAIL uses a verified domain')
                self.stdout.write('4. Check MailerSend dashboard for API errors')
            else:
                self.stdout.write('1. Check EMAIL_BACKEND setting in settings.py')
                self.stdout.write('2. Verify email server credentials')
                self.stdout.write('3. Check firewall/network settings')
            
            self.stdout.write('\n' + '=' * 60 + '\n')
            sys.exit(1)

