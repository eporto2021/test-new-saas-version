from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from djstripe.models import Product

from apps.subscriptions.helpers import cancel_subscription
from apps.users.models import CustomUser
from .models import SubscriptionRequest, SubscriptionAvailability, ProductDemoLink

log = logging.getLogger("test.subscription")


@receiver(post_delete, sender=CustomUser)
def cancel_subscription_on_user_delete(sender, instance: CustomUser, **kwargs):
    if instance.has_active_subscription():
        cancel_subscription(instance.subscription.id)


@receiver(post_save, sender=SubscriptionRequest)
def create_availability_on_request_approval(sender, instance: SubscriptionRequest, created: bool, **kwargs):
    """
    Handle approval of subscription and demo requests.
    
    For subscription requests: Create/update SubscriptionAvailability to enable Subscribe button.
    For demo requests: Send email notification to the user.
    """
    try:
        if instance.status != "approved":
            return

        # Resolve the djstripe Product; if it doesn't exist we can't proceed
        try:
            product = Product.objects.get(id=instance.product_stripe_id)
        except Product.DoesNotExist:
            log.warning(
                "Product %s not found while approving request %s; availability not created",
                instance.product_stripe_id,
                instance.id,
            )
            return

        # Handle based on request type
        if instance.request_type == 'demo':
            # Send demo approval email
            _send_demo_approval_email(instance, product)
        else:
            # Handle subscription request approval
            # Idempotent: unique_together on (stripe_product, user)
            availability, _ = SubscriptionAvailability.objects.update_or_create(
                stripe_product=product,
                user=instance.user,
                defaults={"make_subscription_available": True},
            )
            log.info(
                "SubscriptionAvailability enabled for user %s and product %s",
                instance.user_id,
                product.id,
            )
    except Exception as exc:
        # Never break save pipeline; just log
        log.error(
            "Error handling approved request %s: %s",
            getattr(instance, "id", "unknown"),
            str(exc),
        )


def _send_demo_approval_email(subscription_request: SubscriptionRequest, product: Product):
    """
    Send an email notification when a demo request is approved.
    Includes the demo URL from the request and a Calendly booking link.
    """
    try:
        # Get the project name from settings
        project_name = settings.PROJECT_METADATA.get('NAME', 'Our Platform')
        
        # Get the demo URL from the subscription request (set by admin)
        demo_url = subscription_request.demo_url
        
        # If no demo URL on the request, try to get from ProductDemoLink
        if not demo_url:
            try:
                demo_link = ProductDemoLink.objects.get(
                    stripe_product_id=product.id,
                    is_active=True
                )
                demo_url = demo_link.demo_url
            except ProductDemoLink.DoesNotExist:
                log.warning(
                    "No demo URL found for product %s when approving demo request %s",
                    product.id,
                    subscription_request.id
                )
        
        # Get Calendly link from settings
        calendly_link = settings.PROJECT_METADATA.get('CALENDLY_LINK', 'https://calendly.com/your-link')
        
        # Email subject
        subject = f"Your {product.name} Demo is Ready!"
        
        # Build the email message
        user_name = subscription_request.user.first_name or subscription_request.user.get_full_name() or 'there'
        
        if demo_url:
            message = f"""
Hi {user_name},

Your {product.name} demo is ready. Here is a link to the demo:

{demo_url}

Alternatively, if you'd like to book in a meeting for a live demo or follow up, please book in a time at this link:

{calendly_link}

If you have any questions or need additional assistance, please don't hesitate to reach out to our support team at {settings.PROJECT_METADATA.get('CONTACT_EMAIL', 'support@example.com')}.

Best regards,
The {project_name} Team
            """.strip()
        else:
            # If no demo link exists, send a message with just the booking option
            message = f"""
Hi {user_name},

Your {product.name} demo is ready!

If you'd like to book in a meeting for a live demo or follow up, please book in a time at this link:

{calendly_link}

If you have any questions, please reach out to our support team at {settings.PROJECT_METADATA.get('CONTACT_EMAIL', 'support@example.com')}.

Best regards,
The {project_name} Team
            """.strip()
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[subscription_request.user.email],
            fail_silently=False,
        )
        
        log.info(
            "Demo approval email sent to user %s (%s) for product %s with demo_url=%s",
            subscription_request.user.id,
            subscription_request.user.email,
            product.name,
            demo_url or 'None'
        )
        
    except Exception as e:
        log.error(
            "Failed to send demo approval email for request %s: %s",
            subscription_request.id,
            str(e)
        )
