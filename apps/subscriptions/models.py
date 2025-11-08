import contextlib

from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from djstripe.enums import SubscriptionStatus
from djstripe.models import Customer, Subscription, Product

from apps.subscriptions.wrappers import SubscriptionWrapper


class SubscriptionRequest(models.Model):
    """
    Tracks user requests for subscription trials/demos.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('contacted', _('Contacted')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='subscription_requests'
    )
    product_name = models.CharField(max_length=255)
    product_stripe_id = models.CharField(max_length=255)
    message = models.TextField(blank=True, help_text=_("Optional message from user"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, help_text=_("Internal notes"))
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Subscription Request")
        verbose_name_plural = _("Subscription Requests")
    
    def __str__(self):
        return f"{self.user.email} - {self.product_name} ({self.status})"


class SubscriptionAvailability(models.Model):
    """
    Controls which Stripe products are available for subscription purchase.
    Can be set globally or for specific users.
    """
    
    stripe_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text=_("The Stripe product this availability setting controls")
    )
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("If set, this availability applies only to this specific user. If null, applies globally.")
    )
    make_subscription_available = models.BooleanField(
        default=False,
        help_text=_("When True, shows the Subscribe button for this product. When False, only shows Request Subscription button.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription Availability")
        verbose_name_plural = _("Subscription Availabilities")
        unique_together = ['stripe_product', 'user']
    
    def __str__(self):
        status = "Available" if self.make_subscription_available else "Request Only"
        user_info = f" (User: {self.user.email})" if self.user else " (Global)"
        return f"{self.stripe_product.name} - {status}{user_info}"


class ProductDemoLink(models.Model):
    """
    Stores demo links for subscription products to display on product cards.
    """
    
    product_name = models.CharField(
        max_length=255,
        help_text=_("Name of the subscription product")
    )
    stripe_product_id = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Stripe Product ID (e.g., prod_T9FO1AD2u8s2xX)")
    )
    demo_url = models.URLField(
        max_length=500,
        help_text=_("URL to the demo page or video")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Show/hide the demo link on product card")
    )
    button_text = models.CharField(
        max_length=50,
        default="View Demo",
        help_text=_("Text to display on the demo button")
    )
    open_in_new_tab = models.BooleanField(
        default=True,
        help_text=_("Open demo link in a new browser tab")
    )
    display_order = models.IntegerField(
        default=0,
        help_text=_("Display order (lower numbers appear first)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Product Demo Link")
        verbose_name_plural = _("Product Demo Links")
        ordering = ['display_order', 'product_name']
    
    def __str__(self):
        return f"{self.product_name} - {self.button_text}"


class SubscriptionModelBase(models.Model):
    """
    Helper class to be used with Stripe Subscriptions.

    Assumes that the associated subclass is a django model containing a
    subscription field that is a ForeignKey to a djstripe.Subscription object.
    """

    # subclass should override with appropriate foreign keys as needed
    subscription = models.ForeignKey(
        "djstripe.Subscription",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("The associated Stripe Subscription object, if it exists"),
    )
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    billing_details_last_changed = models.DateTimeField(
        default=timezone.now, help_text=_("Updated every time an event that might trigger billing happens.")
    )
    last_synced_with_stripe = models.DateTimeField(
        null=True, blank=True, help_text=_("Used for determining when to next sync with Stripe.")
    )

    class Meta:
        abstract = True

    @cached_property
    def active_stripe_subscription(self) -> Subscription | None:
        from apps.subscriptions.helpers import subscription_is_active

        if self.subscription and subscription_is_active(self.subscription):
            return self.subscription
        return None

    @cached_property
    def wrapped_subscription(self) -> SubscriptionWrapper | None:
        """
        Returns the current subscription as a SubscriptionWrapper
        """
        if self.subscription:
            return SubscriptionWrapper(self.subscription)
        return None

    def clear_cached_subscription(self):
        """
        Clear the cached subscription object (in case it has changed since the model was created)
        """
        with contextlib.suppress(AttributeError):
            del self.active_stripe_subscription
        with contextlib.suppress(AttributeError):
            del self.wrapped_subscription

    def has_active_subscription(self) -> bool:
        # Check if user has a primary subscription
        if self.active_stripe_subscription is not None:
            return True
        
        # Also check if customer has any active subscriptions
        if self.customer:
            from djstripe.models import Subscription
            from djstripe.enums import SubscriptionStatus
            return Subscription.objects.filter(
                customer=self.customer,
                status__in=[SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]
            ).exists()
        
        return False

    @classmethod
    def get_items_needing_sync(cls):
        return cls.objects.filter(
            Q(last_synced_with_stripe__isnull=True) | Q(last_synced_with_stripe__lt=F("billing_details_last_changed")),
            subscription__status=SubscriptionStatus.active,
        )

    def get_quantity(self) -> int:
        # if you use "per-seat" billing, override this accordingly
        return 1
