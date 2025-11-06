from django import template
from django.urls import reverse
from django.utils.text import slugify
from ..helpers import get_user_accessible_services

register = template.Library()


@register.inclusion_tag('services/nav_services.html', takes_context=True)
def nav_services(context):
    """
    Template tag to include service navigation items.
    """
    request = context['request']
    accessible_services = []
    
    if request.user.is_authenticated:
        accessible_services = get_user_accessible_services(request.user)
    
    return {
        'accessible_services': accessible_services,
        'request': request
    }


@register.simple_tag
def user_accessible_services(user):
    """
    Template tag to get user's accessible services.
    """
    if user.is_authenticated:
        return get_user_accessible_services(user)
    return []


@register.simple_tag
def user_navigation_items(user):
    """
    Template tag to get user's navigation items, avoiding duplicates between services and subscriptions.
    Prioritizes subscriptions over services when both exist for the same product.
    """
    if not user.is_authenticated:
        return []
    
    navigation_items = []
    subscription_slugs = set()
    
    # First, add all active subscriptions
    try:
        from apps.subscriptions.templatetags.subscription_tags import user_active_subscriptions
        subscription_items = user_active_subscriptions(user)
        
        for subscription_item in subscription_items:
            subscription_slug = subscription_item['slug']
            subscription_slugs.add(subscription_slug)
            navigation_items.append({
                'name': subscription_item['name'],
                'slug': subscription_slug,
                'icon': subscription_item['icon'],
                'url': reverse('subscriptions:subscription_service', args=[subscription_slug]),
                'tab_class': f'subscription-{subscription_slug}',
                'type': 'subscription'
            })
    except ImportError:
        # Fallback if subscription tags are not available
        pass
    
    # Then, add services that don't have corresponding subscriptions
    accessible_services = get_user_accessible_services(user)
    
    for service in accessible_services:
        # Only add if there's no corresponding subscription
        if service.slug not in subscription_slugs:
            navigation_items.append({
                'name': service.name,
                'slug': service.slug,
                'icon': service.icon,
                'url': reverse('services:generic_service', args=[service.slug]),
                'tab_class': f'service-{service.slug}',
                'type': 'service'
            })
    
    return navigation_items
