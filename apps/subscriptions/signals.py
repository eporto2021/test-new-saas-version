from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import logging

from djstripe.models import Product

from apps.subscriptions.helpers import cancel_subscription
from apps.users.models import CustomUser
from .models import SubscriptionRequest, SubscriptionAvailability

log = logging.getLogger("test.subscription")


@receiver(post_delete, sender=CustomUser)
def cancel_subscription_on_user_delete(sender, instance: CustomUser, **kwargs):
    if instance.has_active_subscription():
        cancel_subscription(instance.subscription.id)


@receiver(post_save, sender=SubscriptionRequest)
def create_availability_on_request_approval(sender, instance: SubscriptionRequest, created: bool, **kwargs):
    """
    Ensure a user's approved subscription request enables the Subscribe button.

    Whenever a SubscriptionRequest is saved with status 'approved', create or
    update a SubscriptionAvailability record linking the user and the Stripe
    Product so templates can show the Subscribe button.
    """
    try:
        if instance.status != "approved":
            return

        # Resolve the djstripe Product; if it doesn't exist we can't enable availability
        try:
            product = Product.objects.get(id=instance.product_stripe_id)
        except Product.DoesNotExist:
            log.warning(
                "Product %s not found while approving request %s; availability not created",
                instance.product_stripe_id,
                instance.id,
            )
            return

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
            "Error creating availability for approved request %s: %s",
            getattr(instance, "id", "unknown"),
            str(exc),
        )
