from __future__ import annotations

import json
from collections.abc import Generator
from dataclasses import asdict, dataclass, field

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import slugify
from djstripe.enums import PlanInterval
from djstripe.models import Price, Product
from drf_spectacular.utils import inline_serializer
from rest_framework.fields import DictField

from apps.utils.billing import get_friendly_currency_amount

from .exceptions import SubscriptionConfigError
from .serializers import PriceSerializer, ProductSerializer


@dataclass
class ProductMetadata:
    """
    Metadata for a Stripe product.
    """

    stripe_id: str
    slug: str
    name: str
    features: list[str]
    price_displays: dict[str:str] = field(default_factory=dict)
    description: str = ""
    is_default: bool = False

    @classmethod
    def from_stripe_product(cls, stripe_product: Product, **kwargs) -> ProductMetadata:
        # Extract features from Stripe marketing_features field
        features = []
        
        # First try to get from marketing_features field (Stripe's built-in field)
        # Since djstripe Product model doesn't store marketing_features, fetch from API
        if hasattr(stripe_product, 'marketing_features') and stripe_product.marketing_features:
            features = [feature.name for feature in stripe_product.marketing_features if hasattr(feature, 'name')]
        else:
            # Fetch marketing_features directly from Stripe API
            try:
                from apps.subscriptions.helpers import get_stripe_module
                stripe = get_stripe_module()
                stripe_api_product = stripe.Product.retrieve(stripe_product.id)
                if hasattr(stripe_api_product, 'marketing_features') and stripe_api_product.marketing_features:
                    features = [feature['name'] for feature in stripe_api_product.marketing_features]
            except Exception:
                # If API fetch fails, continue to fallback methods
                pass
        
        # Fallback to metadata fields if still no features
        if not features and stripe_product.metadata and 'features' in stripe_product.metadata:
            # Features stored as JSON string in Stripe metadata
            try:
                features = json.loads(stripe_product.metadata['features'])
            except (json.JSONDecodeError, TypeError):
                # Fallback: treat as comma-separated string
                features = stripe_product.metadata['features'].split(',')
        elif not features and stripe_product.metadata and 'marketing_features' in stripe_product.metadata:
            # Alternative field name in metadata
            try:
                features = json.loads(stripe_product.metadata['marketing_features'])
            except (json.JSONDecodeError, TypeError):
                features = stripe_product.metadata['marketing_features'].split(',')
        
        # Clean up features (remove extra whitespace)
        features = [f.strip() for f in features if f.strip()]
        
        # Get price displays for different intervals
        price_displays = {}
        for price in stripe_product.prices.filter(active=True):
            if price.recurring and price.recurring.get('interval'):
                interval = price.recurring['interval']
                price_displays[interval] = get_friendly_currency_amount(price)
        
        defaults = dict(
            stripe_id=stripe_product.id,
            slug=slugify(stripe_product.name),
            name=stripe_product.name,
            features=features,
            price_displays=price_displays,
            description=stripe_product.description or f"The {stripe_product.name} plan"
        )
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def serializer(cls):
        """Serializer used for schema generation"""
        from drf_spectacular.utils import inline_serializer
        from rest_framework import serializers

        return inline_serializer(
            "ProductMetadata",
            {
                "stripe_id": serializers.CharField(),
                "slug": serializers.CharField(),
                "name": serializers.CharField(),
                "features": serializers.ListField(child=serializers.CharField()),
                "price_displays": serializers.DictField(child=serializers.CharField()),
                "description": serializers.CharField(),
                "is_default": serializers.BooleanField(),
            },
        )


@dataclass
class ProductWithMetadata:
    """
    Connects a Stripe product to its ProductMetadata.
    """

    product: Product
    metadata: ProductMetadata

    @property
    def stripe_id(self) -> str:
        return self.metadata.stripe_id or self.product.id

    def _get_price(self, interval: str, fail_hard: bool = True) -> Price | None:
        if self.product:
            try:
                return self.product.prices.get(
                    recurring__interval=interval,
                    recurring__interval_count=1,
                    active=True,
                    livemode=settings.STRIPE_LIVE_MODE,
                )
            except (Price.DoesNotExist, Price.MultipleObjectsReturned):
                if fail_hard:
                    raise SubscriptionConfigError(
                        _(
                            f'Unable to select a "{interval}" plan for {self.product}. '
                            "Have you setup your Stripe objects and run ./manage.py bootstrap_subscriptions? "
                            "You can also hide this plan interval by removing it from ACTIVE_PLAN_INTERVALS in "
                            "apps/subscriptions/metadata.py"
                        )
                    ) from None
                else:
                    return None

    def get_price_display(self, price: Price) -> str:
        # if the price display info has been explicitly overridden, use that
        if price.recurring["interval"] in self.metadata.price_displays:
            return self.metadata.price_displays[price.recurring["interval"]]
        else:
            # otherwise get it from the price
            return get_friendly_currency_amount(price)

    def to_dict(self):
        """
        :return: a JSON-serializable dictionary for this object,
        usable in an API.
        """

        def _serialized_price_or_none(price):
            return PriceSerializer(price, context={"product_metadata": self}).data if price else None

        return {
            "product": {"id": self.product.id, "name": self.product.name},
            "metadata": asdict(self.metadata),
            "active_prices": {
                interval: _serialized_price_or_none(self._get_price(interval, fail_hard=False))
                for interval in ACTIVE_PLAN_INTERVALS
            },
        }

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DjangoJSONEncoder)

    @classmethod
    def serializer(cls):
        """Serializer used for schema generation"""
        return inline_serializer(
            "ProductWithMetadata",
            {
                "product": ProductSerializer(),
                "metadata": ProductMetadata.serializer(),
                "active_prices": DictField(child=PriceSerializer()),
            },
        )


@dataclass
class PlanIntervalMetadata:
    """
    Metadata for a Stripe product.
    """

    interval: str
    name: str
    help_text: str


def get_plan_name_for_interval(interval: str) -> str:
    # Use lazy evaluation to avoid import-time translation calls
    from django.utils.translation import gettext_lazy as _
    
    # Create the mapping inside the function to avoid import-time evaluation
    interval_names = {
        PlanInterval.year: _("Annual"),
        PlanInterval.month: _("Monthly"),
        PlanInterval.week: _("Weekly"),
        PlanInterval.day: _("Daily"),
    }
    return interval_names.get(interval, _("Custom"))


def get_help_text_for_interval(interval):
    # Use lazy evaluation to avoid import-time translation calls
    from django.utils.translation import gettext_lazy as _
    
    # Create the mapping inside the function to avoid import-time evaluation
    help_texts = {
        PlanInterval.year: _("You're getting two months free by choosing an Annual plan!"),
        PlanInterval.month: _("Upgrade to annual pricing to get two free months."),
    }
    return help_texts.get(interval, _("Good choice!"))


def get_active_plan_interval_metadata() -> list[PlanIntervalMetadata]:
    return [
        PlanIntervalMetadata(
            interval=interval,
            name=get_plan_name_for_interval(interval),
            help_text=get_help_text_for_interval(interval),
        )
        for interval in ACTIVE_PLAN_INTERVALS
    ]


# Active plan intervals. Only allowed values are "PlanInterval.month" and "PlanInterval.year"
# Remove one of them to only allow monthly/annual pricing.
# The first element is considered the default

ACTIVE_PLAN_INTERVALS = [
    PlanInterval.week,
    PlanInterval.year,
    PlanInterval.month,
]

# Product IDs are now defined in settings.py (development) and settings_production.py (production)
# No hardcoded values here - everything comes from Django settings
ACTIVE_PRODUCTS = getattr(settings, 'ACTIVE_PRODUCTS', [])

# Convert list of product IDs to set for faster lookup
ACTIVE_PRODUCT_IDS = set(ACTIVE_PRODUCTS)


def get_active_products_with_metadata() -> Generator[ProductWithMetadata]:
    """
    Get active products with metadata.
    
    Products should be synced to the database using:
        python manage.py djstripe_sync_models product price
    
    This is automatically run during deployment via the release command.
    
    Only products explicitly listed in ACTIVE_PRODUCTS will be displayed.
    If ACTIVE_PRODUCTS is empty, no products will be shown.
    """
    from django.utils.translation import gettext_lazy as _
    
    # Only show products explicitly listed in ACTIVE_PRODUCTS
    # If the list is empty, show nothing (not all products in DB)
    if ACTIVE_PRODUCTS:
        for product_id in ACTIVE_PRODUCTS:
            try:
                product = Product.objects.get(id=product_id)
                yield ProductWithMetadata(
                    product=product,
                    metadata=ProductMetadata.from_stripe_product(product),
                )
            except Product.DoesNotExist:
                raise SubscriptionConfigError(
                    _(
                        f'No Product with ID "{product_id}" found in database! '
                        f'This product ID is in the ACTIVE_PRODUCTS list. '
                        f'Run: python manage.py djstripe_sync_models product price'
                    )
                ) from None
    # If ACTIVE_PRODUCTS is empty, return nothing (generator will be empty)


def get_product_with_metadata(djstripe_product: Product) -> ProductWithMetadata:
    if djstripe_product.id in ACTIVE_PRODUCT_IDS:
        return ProductWithMetadata(product=djstripe_product, metadata=ProductMetadata.from_stripe_product(djstripe_product))
    else:
        return ProductWithMetadata(
            product=djstripe_product, metadata=ProductMetadata.from_stripe_product(djstripe_product)
        )
