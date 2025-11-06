from djstripe.models import Price, Product, Subscription, SubscriptionItem
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


def safe_human_readable_price(price_obj):
    """
    Safely get human readable price, handling cases where tiers is None.
    """
    try:
        return str(price_obj.human_readable_price)
    except (TypeError, AttributeError, IndexError):
        # Handle cases where tiers is None or other issues
        if price_obj.unit_amount is not None:
            # Format the price manually if human_readable_price fails
            amount = price_obj.unit_amount / 100  # Convert from cents
            currency_symbol = "$" if price_obj.currency == "usd" else price_obj.currency.upper()
            return f"{currency_symbol}{amount:.2f}"
        return "Unknown"


class PriceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    human_readable_price = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.STR)
    def get_human_readable_price(self, obj):
        # this needs to be here because djstripe can return a proxy object which can't be serialized
        return safe_human_readable_price(obj)

    @extend_schema_field(OpenApiTypes.STR)
    def get_payment_amount(self, obj):
        if self.context.get("product_metadata", None):
            return self.context["product_metadata"].get_price_display(obj)
        return safe_human_readable_price(obj)

    class Meta:
        model = Price
        fields = ("id", "product_name", "human_readable_price", "payment_amount", "nickname", "unit_amount")


class SubscriptionItemSerializer(serializers.ModelSerializer):
    price = PriceSerializer()

    class Meta:
        model = SubscriptionItem
        fields = ("id", "price", "quantity")


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    A serializer for Subscriptions which uses the SubscriptionWrapper object under the hood
    """

    items = SubscriptionItemSerializer(many=True)
    display_name = serializers.CharField()
    billing_interval = serializers.CharField()

    class Meta:
        # we use Subscription instead of SubscriptionWrapper so DRF can infer the model-based fields automatically
        model = Subscription
        fields = (
            "id",
            "display_name",
            "start_date",
            "billing_interval",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "start_date",
            "status",
            "quantity",
            "items",
        )


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name")
