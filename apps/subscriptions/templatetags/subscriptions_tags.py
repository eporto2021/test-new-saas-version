from django import template
from djstripe.models import SubscriptionItem, Price

from apps.utils.billing import get_friendly_currency_amount

register = template.Library()


@register.simple_tag
def render_subscription_item_price(subscription_item: SubscriptionItem, currency: str):
    if subscription_item.price.currency != currency:
        return get_friendly_currency_amount(subscription_item.price, currency)
    return subscription_item.price.human_readable_price


@register.filter
def safe_human_readable_price(price):
    """
    Safely render human readable price, handling cases where tiers is None.
    """
    if not isinstance(price, Price):
        return "Unknown"
    
    try:
        return price.human_readable_price
    except (TypeError, AttributeError, IndexError):
        # Handle cases where tiers is None or other issues
        if price.unit_amount is not None:
            # Format the price manually if human_readable_price fails
            amount = price.unit_amount / 100  # Convert from cents
            currency_symbol = "$" if price.currency == "usd" else price.currency.upper()
            return f"{currency_symbol}{amount:.2f}"
        return "Unknown"
