import logging

from django.core.mail import mail_admins
from djstripe.event_handlers import djstripe_receiver
from djstripe.models import Customer, Price, Subscription

from apps.users.models import CustomUser

from .helpers import provision_subscription

log = logging.getLogger("test.subscription")


@djstripe_receiver("checkout.session.completed")
def checkout_session_completed(event, **kwargs):
    """
    This webhook is called when a customer signs up for a subscription via Stripe Checkout.

    We must then provision the subscription and assign it to the appropriate user/team.
    """
    session = event.data["object"]
    # only process subscriptions created by this module or that have a subscription set
    if session["metadata"].get("source") == "subscriptions" or session.get("subscription"):
        client_reference_id = session.get("client_reference_id")
        subscription_id = session.get("subscription")
        subscription_holder = CustomUser.objects.get(id=client_reference_id)
        provision_subscription(subscription_holder, subscription_id)
        
        # Update service access for the user
        from apps.services.helpers import update_user_service_access_from_subscription
        from djstripe.models import Subscription
        try:
            djstripe_subscription = Subscription.objects.get(id=subscription_id)
            update_user_service_access_from_subscription(subscription_holder, djstripe_subscription)
        except Subscription.DoesNotExist:
            log.error(f"Subscription {subscription_id} not found for service access update")


@djstripe_receiver("customer.subscription.updated")
def update_customer_subscription(event, **kwargs):
    """
    This webhook is called when a customer updates their subscription via the Stripe
    billing portal.

    There are a few scenarios this can happen - if they are upgrading, downgrading
    cancelling (at the period end) or renewing after a cancellation.

    We update the subscription in place based on the possible fields, and
    these updates automatically trickle down to the user/team that holds the subscription.

    Stripe docs: https://stripe.com/docs/customer-management/integrate-customer-portal#webhooks
    """
    subscription_data = event.data["object"]
    subscription_id = subscription_data["id"]
    
    # Update service access when subscription changes
    try:
        djstripe_subscription = Subscription.objects.get(id=subscription_id)
        
        # Find the user associated with this subscription
        customer = djstripe_subscription.customer
        try:
            user = CustomUser.objects.get(customer=customer)
            
            # Update service access
            from apps.services.helpers import update_user_service_access_from_subscription
            update_user_service_access_from_subscription(user, djstripe_subscription)
        except CustomUser.DoesNotExist:
            log.error(f"User not found for customer {customer.id}")
    except Subscription.DoesNotExist:
        log.error(f"Subscription {subscription_id} not found for update")
    
    # check if we can handle this change
    if has_multiple_items(event.data):
        logging.warning("Not processing changes to Stripe subscription because it has multiple products.")
        return

    new_price = get_price_data(event.data)
    subscription_id = get_subscription_id(event.data)

    # find associated subscription and change the price details accordingly
    dj_subscription = Subscription.objects.get(id=subscription_id)
    subscription_item = dj_subscription.items.get()
    subscription_item.price = Price.objects.get(id=new_price["id"])
    subscription_item.save()
    dj_subscription.cancel_at_period_end = get_cancel_at_period_end(event.data)
    dj_subscription.save()


@djstripe_receiver("customer.subscription.deleted")
def handle_subscription_deleted(event, **kwargs):
    """
    Ensure local state (service access + notifications) is updated when Stripe fully cancels a subscription.
    """
    subscription_data = event.data["object"]
    subscription_id = subscription_data["id"]
    
    djstripe_subscription = None
    try:
        djstripe_subscription = Subscription.objects.get(id=subscription_id)
    except Subscription.DoesNotExist:
        # Fallback to syncing directly from the webhook payload
        try:
            djstripe_subscription = Subscription.sync_from_stripe_data(subscription_data)
        except Exception as exc:
            log.error(f"Unable to sync subscription {subscription_id} on delete webhook: {exc}")
    
    if djstripe_subscription and djstripe_subscription.customer:
        from apps.services.helpers import update_user_service_access_from_subscription, revoke_service_access
        from apps.services.models import Service, UserServiceAccess
        from django.utils.text import slugify
        
        try:
            user = CustomUser.objects.get(customer=djstripe_subscription.customer)
            update_user_service_access_from_subscription(user, djstripe_subscription)
            
            # Explicitly revoke any lingering service access records tied to this subscription's products
            product_ids = []
            try:
                for item in subscription_data.get("items", {}).get("data", []):
                    price_data = item.get("price") or {}
                    product_id = price_data.get("product")
                    if product_id:
                        product_ids.append(product_id)
            except Exception:
                pass
            
            if product_ids:
                UserServiceAccess.objects.filter(
                    user=user,
                    service__stripe_product__id__in=product_ids
                ).delete()
            else:
                # Fallback: derive slug from product name if available and revoke by slug
                product_name = subscription_data.get("items", {}).get("data", [{}])[0].get("plan", {}).get("product")
                if product_name:
                    slug = slugify(product_name)
                    revoke_service_access(user, slug)
        except CustomUser.DoesNotExist:
            log.error(f"User not found for customer {djstripe_subscription.customer.id} during subscription delete")
    
    # Notify admins so they still get visibility of the cancellation
    try:
        customer_email = Customer.objects.get(id=subscription_data["customer"]).email
    except Customer.DoesNotExist:
        customer_email = "unavailable"
    
    mail_admins(
        "Someone just canceled their subscription!",
        f"Their email was {customer_email}",
        fail_silently=True,
    )


def has_multiple_items(stripe_event_data):
    return len(stripe_event_data["object"]["items"]["data"]) > 1


def get_price_data(stripe_event_data):
    return stripe_event_data["object"]["items"]["data"][0]["price"]


def get_subscription_id(stripe_event_data):
    return stripe_event_data["object"]["items"]["data"][0]["subscription"]


def get_cancel_at_period_end(stripe_event_data):
    return stripe_event_data["object"]["cancel_at_period_end"]
