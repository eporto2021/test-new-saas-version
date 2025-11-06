"""
Simple email backend that prints emails directly to stdout for Docker visibility.
"""
import sys
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage


class PrintEmailBackend(BaseEmailBackend):
    """
    Email backend that prints emails directly to stdout for Docker visibility.
    """
    
    def send_messages(self, email_messages):
        """
        Print all email messages to stdout.
        """
        if not email_messages:
            return 0
        
        for message in email_messages:
            self._print_email(message)
        
        return len(email_messages)
    
    def _print_email(self, message):
        """
        Print a single email message to stdout.
        """
        print("\n" + "="*80)
        print("📧 EMAIL SENT")
        print("="*80)
        print(f"To: {', '.join(message.to)}")
        print(f"From: {message.from_email}")
        print(f"Subject: {message.subject}")
        print("-"*80)
        print("BODY:")
        print("-"*80)
        
        # Print the email body
        if hasattr(message, 'body') and message.body:
            print(message.body)
        else:
            # For multipart messages, print the text content
            for part in message.message.walk():
                if part.get_content_type() == "text/plain":
                    print(part.get_payload(decode=True).decode('utf-8'))
                    break
        
        print("="*80)
        print("END EMAIL")
        print("="*80 + "\n")
        
        # Force flush to ensure it appears in Docker logs
        sys.stdout.flush()