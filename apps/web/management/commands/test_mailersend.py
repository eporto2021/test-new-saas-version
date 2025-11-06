from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = "Test MailerSend email configuration by sending a test email"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email address to send test email to")
        parser.add_argument(
            "--template", 
            type=str, 
            default="simple",
            choices=["simple", "html", "account_creation"],
            help="Type of test email to send"
        )

    def handle(self, email, template, **options):
        self.stdout.write(f"Testing MailerSend configuration...")
        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"From email: {settings.DEFAULT_FROM_EMAIL}")
        
        if template == "simple":
            subject = "MailerSend Test Email"
            message = f"""
This is a test email from your Django application using MailerSend.

If you receive this email, your MailerSend configuration is working correctly!

Email backend: {settings.EMAIL_BACKEND}
From: {settings.DEFAULT_FROM_EMAIL}
To: {email}

Best regards,
Your Django App
            """.strip()
            html_message = None
            
        elif template == "html":
            subject = "MailerSend HTML Test Email"
            message = "This is a plain text version of the HTML email."
            html_message = f"""
            <html>
            <body>
                <h2>MailerSend HTML Test Email</h2>
                <p>This is a test email with <strong>HTML formatting</strong> from your Django application using MailerSend.</p>
                <p>If you receive this email, your MailerSend configuration is working correctly!</p>
                <ul>
                    <li>Email backend: {settings.EMAIL_BACKEND}</li>
                    <li>From: {settings.DEFAULT_FROM_EMAIL}</li>
                    <li>To: {email}</li>
                </ul>
                <p>Best regards,<br>Your Django App</p>
            </body>
            </html>
            """
            
        elif template == "account_creation":
            subject = "Account Creation Test Email"
            message = f"""
Welcome to our platform!

This is a test of the account creation email template.

Your account has been created successfully.

Email: {email}
From: {settings.DEFAULT_FROM_EMAIL}

Thank you for joining us!
            """.strip()
            html_message = None

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Test email sent successfully to {email}")
            )
            self.stdout.write(f"Subject: {subject}")
            self.stdout.write(f"Template: {template}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to send test email: {str(e)}")
            )
            self.stdout.write("Check your MailerSend configuration:")
            self.stdout.write("1. Verify MAILERSEND_API_KEY is set correctly")
            self.stdout.write("2. Ensure your domain is verified in MailerSend")
            self.stdout.write("3. Check that DEFAULT_FROM_EMAIL uses a verified domain")
            raise
