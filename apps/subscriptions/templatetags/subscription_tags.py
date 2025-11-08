from django import template
from django.utils.text import slugify
from djstripe.models import Subscription
from djstripe.enums import SubscriptionStatus

from ..models import SubscriptionRequest, SubscriptionAvailability

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a variable key.
    
    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.simple_tag
def user_active_subscriptions(user):
    """
    Template tag to get user's active subscriptions for navigation.
    
    Returns:
        List of subscription data for navigation display
    """
    if not user.is_authenticated or not user.customer:
        return []
    
    subscriptions = Subscription.objects.filter(
        customer=user.customer,
        status__in=[SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]
    ).order_by('-created')
    
    subscription_nav_items = []
    for subscription in subscriptions:
        # Get the first product from the subscription
        if subscription.items.exists():
            first_item = subscription.items.first()
            product = first_item.price.product
            
            subscription_nav_items.append({
                'subscription': subscription,
                'product': product,
                'name': product.name,
                'slug': slugify(product.name),
                'icon': 'fa fa-star',  # Default icon, can be customized
            })
    
    return subscription_nav_items


@register.simple_tag
def user_has_requested_subscription(user, product_id):
    """
    Check if user has already requested a subscription for a specific product.
    
    Args:
        user: The user to check
        product_id: The Stripe product ID to check for
        
    Returns:
        bool: True if user has requested this subscription, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    return SubscriptionRequest.objects.filter(
        user=user,
        product_stripe_id=product_id
    ).exists()


@register.simple_tag
def is_subscription_available_for_purchase(product_id, user=None):
    """
    Check if a subscription is available for direct purchase (shows Subscribe button).
    Checks SubscriptionAvailability settings for the product.
    
    Args:
        product_id: The Stripe product ID to check
        user: The user to check availability for (optional)
        
    Returns:
        bool: True if subscription is available for purchase, False if only request is allowed
    """
    if not user or not user.is_authenticated:
        return False
    
    # First check for user-specific availability
    try:
        user_availability = SubscriptionAvailability.objects.get(
            stripe_product__id=product_id,
            user=user
        )
        return user_availability.make_subscription_available
    except SubscriptionAvailability.DoesNotExist:
        pass
    
    # If no user-specific setting, check global availability
    try:
        global_availability = SubscriptionAvailability.objects.get(
            stripe_product__id=product_id,
            user=None
        )
        return global_availability.make_subscription_available
    except SubscriptionAvailability.DoesNotExist:
        # Default to False if no availability setting exists
        return False


@register.simple_tag
def user_has_active_subscription_for_product(user, product_id):
    """
    Check if user has an active subscription for a specific product.
    
    Args:
        user: The user to check
        product_id: The Stripe product ID to check for
        
    Returns:
        bool: True if user has an active subscription for this product, False otherwise
    """
    if not user.is_authenticated or not user.customer:
        return False
    
    # Check if user has any active subscriptions for this product
    active_subscriptions = Subscription.objects.filter(
        customer=user.customer,
        status__in=[SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]
    )
    
    for subscription in active_subscriptions:
        # Check if any subscription item matches this product
        for item in subscription.items.all():
            if item.price.product.id == product_id:
                return True
    
    return False
