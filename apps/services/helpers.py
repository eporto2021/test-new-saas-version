from django.utils import timezone
from django.utils.text import slugify
from djstripe.models import Subscription, Product
from djstripe.enums import SubscriptionStatus

from .models import Service, UserServiceAccess
from apps.users.models import CustomUser


def grant_service_access(user: CustomUser, service_slug: str, subscription: Subscription = None):
    """
    Grant a user access to a specific service.
    
    Args:
        user: The user to grant access to
        service_slug: The slug of the service
        subscription: The subscription that grants this access (optional)
    """
    try:
        service = Service.objects.get(slug=service_slug, is_active=True)
    except Service.DoesNotExist:
        return False
    
    # Create or update the access
    access, created = UserServiceAccess.objects.get_or_create(
        user=user,
        service=service,
        defaults={
            'subscription': subscription,
            'is_active': True,
            'granted_at': timezone.now()
        }
    )
    
    if not created:
        # Update existing access
        access.subscription = subscription
        access.is_active = True
        access.granted_at = timezone.now()
        access.save()
    
    return True


def revoke_service_access(user: CustomUser, service_slug: str):
    """
    Revoke a user's access to a specific service.
    
    Args:
        user: The user to revoke access from
        service_slug: The slug of the service
    """
    try:
        service = Service.objects.get(slug=service_slug)
    except Service.DoesNotExist:
        return False
    
    UserServiceAccess.objects.filter(
        user=user,
        service=service
    ).update(is_active=False)
    
    return True


def update_user_service_access_from_subscription(user: CustomUser, subscription: Subscription):
    """
    Update a user's service access based on their active subscription.
    This should be called when a subscription is created, updated, or cancelled.
    
    Args:
        user: The user whose access should be updated
        subscription: The subscription to process
    """
    if not subscription:
        return
    
    # Get the service associated with this subscription's product
    try:
        service = Service.objects.get(
            stripe_product=subscription.items.first().price.product,
            is_active=True
        )
    except (Service.DoesNotExist, AttributeError):
        # No service configured for this product
        return
    
    # Check if subscription is active
    is_subscription_active = subscription.status in [
        SubscriptionStatus.active,
        SubscriptionStatus.trialing,
        SubscriptionStatus.past_due
    ]
    
    if is_subscription_active:
        # Grant access
        grant_service_access(user, service.slug, subscription)
    else:
        # Revoke access
        revoke_service_access(user, service.slug)


def get_user_accessible_services(user: CustomUser):
    """
    Get all services that a user has access to.
    
    Args:
        user: The user to check access for
        
    Returns:
        QuerySet of Service objects the user has access to
    """
    if not user.is_authenticated:
        return Service.objects.none()
    
    accessible_service_ids = UserServiceAccess.objects.filter(
        user=user,
        is_active=True
    ).values_list('service_id', flat=True)
    
    return Service.objects.filter(
        id__in=accessible_service_ids,
        is_active=True
    ).order_by('order', 'name')


def user_has_service_access(user: CustomUser, service_slug: str) -> bool:
    """
    Check if a user has access to a specific service.
    
    Args:
        user: The user to check
        service_slug: The slug of the service
        
    Returns:
        True if user has access, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    try:
        access = UserServiceAccess.objects.get(
            user=user,
            service__slug=service_slug,
            is_active=True
        )
        return access.is_valid
    except UserServiceAccess.DoesNotExist:
        return False


def get_or_create_service_from_product(product: Product) -> Service:
    """
    Get or create a Service from a Stripe Product.
    
    Args:
        product: The Stripe Product
        
    Returns:
        Service object
    """
    product_slug = slugify(product.name)
    
    service, created = Service.objects.get_or_create(
        stripe_product=product,
        defaults={
            'name': product.name,
            'slug': product_slug,
            'description': product.description or f"Access to {product.name}",
            'icon': 'fa-solid fa-cube',
            'is_active': True,
            'order': 0
        }
    )
    
    return service
