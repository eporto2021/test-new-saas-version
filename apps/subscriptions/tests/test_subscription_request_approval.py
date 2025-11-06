"""
Tests for subscription request approval functionality.

This module tests the complete flow:
1. User requests a subscription
2. Admin approves the request
3. User sees the Subscribe button instead of Request Submitted message
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.template import Context, Template
from djstripe.models import Product, Price
from djstripe import enums

from apps.subscriptions.models import SubscriptionRequest, SubscriptionAvailability
from apps.subscriptions.templatetags.subscription_tags import (
    is_subscription_available_for_purchase,
    user_has_requested_subscription
)

User = get_user_model()


class SubscriptionRequestApprovalTests(TestCase):
    """Test the complete subscription request approval flow."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser@example.com", password="testpass123")

        # Create a test Stripe product and price
        self.stripe_product = Product.objects.create(
            id="prod_test_approval",
            name="Test Approval Product",
            description="A product for testing approval flow",
            active=True
        )
        
        self.stripe_price = Price.objects.create(
            id="price_test_approval",
            product=self.stripe_product,
            currency="usd",
            unit_amount=1000,  # $10.00
            active=True,
            type=enums.PriceType.recurring,
            recurring={
                "interval": "month",
                "interval_count": 1
            }
        )
        
        # Set the default price
        self.stripe_product.default_price = self.stripe_price
        self.stripe_product.save()

    def test_initial_state_no_request_no_availability(self):
        """Test initial state - no request, no availability."""
        # User should not have requested this subscription
        self.assertFalse(user_has_requested_subscription(self.user, self.stripe_product.id))
        
        # Subscription should not be available for purchase
        self.assertFalse(is_subscription_available_for_purchase(self.stripe_product.id, self.user))

    @override_settings(ACTIVE_PRODUCTS=[])
    def test_user_requests_subscription(self):
        """Test user can request a subscription."""
        # User requests subscription
        response = self.client.post(
            reverse('subscriptions:request_subscription', args=[self.stripe_product.id]),
            {'message': 'I would like to subscribe to this product'}
        )
        
        # Should redirect to ecommerce home
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('ecommerce:ecommerce_home'))
        
        # SubscriptionRequest should be created
        request = SubscriptionRequest.objects.get(
            user=self.user,
            product_stripe_id=self.stripe_product.id
        )
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.message, 'I would like to subscribe to this product')
        
        # User should now have requested this subscription
        self.assertTrue(user_has_requested_subscription(self.user, self.stripe_product.id))
        
        # But subscription should still not be available for purchase
        self.assertFalse(is_subscription_available_for_purchase(self.stripe_product.id, self.user))

    def test_admin_approves_request_creates_availability(self):
        """Test that admin approval creates SubscriptionAvailability record."""
        # First, create a subscription request
        subscription_request = SubscriptionRequest.objects.create(
            user=self.user,
            product_name=self.stripe_product.name,
            product_stripe_id=self.stripe_product.id,
            message="Please approve this subscription",
            status='pending'
        )
        
        # Verify no availability record exists yet
        self.assertFalse(
            SubscriptionAvailability.objects.filter(
                stripe_product=self.stripe_product,
                user=self.user
            ).exists()
        )
        
        # Simulate admin approval by calling the admin action
        from apps.subscriptions.admin import SubscriptionRequestAdmin
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.http import HttpRequest
        
        # Create a mock request for the admin action
        request = HttpRequest()
        request.user = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="adminpass123"
        )
        request.session = {}
        request._messages = FallbackStorage(request)
        
        # Create admin instance and call the action
        admin = SubscriptionRequestAdmin(SubscriptionRequest, AdminSite())
        queryset = SubscriptionRequest.objects.filter(id=subscription_request.id)
        
        # Call the mark_approved action
        admin.mark_approved(request, queryset)
        
        # Refresh from database
        subscription_request.refresh_from_db()
        
        # Request status should be approved
        self.assertEqual(subscription_request.status, 'approved')
        
        # SubscriptionAvailability should be created
        availability = SubscriptionAvailability.objects.get(
            stripe_product=self.stripe_product,
            user=self.user
        )
        self.assertTrue(availability.make_subscription_available)
        
        # Now subscription should be available for purchase
        self.assertTrue(is_subscription_available_for_purchase(self.stripe_product.id, self.user))

    def test_template_logic_after_approval(self):
        """Test that template shows Subscribe button after approval."""
        # Create approved subscription request and availability
        subscription_request = SubscriptionRequest.objects.create(
            user=self.user,
            product_name=self.stripe_product.name,
            product_stripe_id=self.stripe_product.id,
            message="Approved request",
            status='approved'
        )
        
        SubscriptionAvailability.objects.create(
            stripe_product=self.stripe_product,
            user=self.user,
            make_subscription_available=True
        )
        
        # Test template logic
        template_code = """
        {% load subscription_tags %}
        {% is_subscription_available_for_purchase product_id user as is_available %}
        {% user_has_requested_subscription user product_id as has_requested %}
        
        {% if is_available %}
            SUBSCRIBE_BUTTON
        {% elif has_requested %}
            REQUEST_SUBMITTED
        {% else %}
            REQUEST_BUTTON
        {% endif %}
        """
        
        template = Template(template_code)
        context = Context({
            'user': self.user,
            'product_id': self.stripe_product.id
        })
        
        result = template.render(context).strip()
        self.assertEqual(result, 'SUBSCRIBE_BUTTON')

    def test_template_logic_before_approval(self):
        """Test that template shows Request Submitted message before approval."""
        # Create pending subscription request (no availability)
        subscription_request = SubscriptionRequest.objects.create(
            user=self.user,
            product_name=self.stripe_product.name,
            product_stripe_id=self.stripe_product.id,
            message="Pending request",
            status='pending'
        )
        
        # Test template logic
        template_code = """
        {% load subscription_tags %}
        {% is_subscription_available_for_purchase product_id user as is_available %}
        {% user_has_requested_subscription user product_id as has_requested %}
        
        {% if is_available %}
            SUBSCRIBE_BUTTON
        {% elif has_requested %}
            REQUEST_SUBMITTED
        {% else %}
            REQUEST_BUTTON
        {% endif %}
        """
        
        template = Template(template_code)
        context = Context({
            'user': self.user,
            'product_id': self.stripe_product.id
        })
        
        result = template.render(context).strip()
        self.assertEqual(result, 'REQUEST_SUBMITTED')

    def test_template_logic_no_request(self):
        """Test that template shows Request button when no request exists."""
        # No subscription request or availability
        
        # Test template logic
        template_code = """
        {% load subscription_tags %}
        {% is_subscription_available_for_purchase product_id user as is_available %}
        {% user_has_requested_subscription user product_id as has_requested %}
        
        {% if is_available %}
            SUBSCRIBE_BUTTON
        {% elif has_requested %}
            REQUEST_SUBMITTED
        {% else %}
            REQUEST_BUTTON
        {% endif %}
        """
        
        template = Template(template_code)
        context = Context({
            'user': self.user,
            'product_id': self.stripe_product.id
        })
        
        result = template.render(context).strip()
        self.assertEqual(result, 'REQUEST_BUTTON')

    def test_global_availability_overrides_user_specific(self):
        """Test that global availability settings work."""
        # Create global availability (no user specified)
        SubscriptionAvailability.objects.create(
            stripe_product=self.stripe_product,
            user=None,  # Global setting
            make_subscription_available=True
        )
        
        # Even without a user-specific setting, subscription should be available
        self.assertTrue(is_subscription_available_for_purchase(self.stripe_product.id, self.user))

    def test_user_specific_availability_overrides_global(self):
        """Test that user-specific availability overrides global settings."""
        # Create global availability (disabled)
        SubscriptionAvailability.objects.create(
            stripe_product=self.stripe_product,
            user=None,  # Global setting
            make_subscription_available=False
        )
        
        # Create user-specific availability (enabled)
        SubscriptionAvailability.objects.create(
            stripe_product=self.stripe_product,
            user=self.user,
            make_subscription_available=True
        )
        
        # User-specific setting should take precedence
        self.assertTrue(is_subscription_available_for_purchase(self.stripe_product.id, self.user))

    def test_approval_handles_missing_product_gracefully(self):
        """Test that approval handles missing Stripe products gracefully."""
        # Create subscription request with non-existent product ID
        subscription_request = SubscriptionRequest.objects.create(
            user=self.user,
            product_name="Non-existent Product",
            product_stripe_id="prod_nonexistent",
            message="Request for non-existent product",
            status='pending'
        )
        
        # Simulate admin approval
        from apps.subscriptions.admin import SubscriptionRequestAdmin
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.user = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="adminpass123"
        )
        request.session = {}
        request._messages = FallbackStorage(request)
        
        admin = SubscriptionRequestAdmin(SubscriptionRequest, AdminSite())
        queryset = SubscriptionRequest.objects.filter(id=subscription_request.id)
        
        # This should not raise an exception
        admin.mark_approved(request, queryset)
        
        # Request should still be approved
        subscription_request.refresh_from_db()
        self.assertEqual(subscription_request.status, 'approved')
        
        # But no availability record should be created
        self.assertFalse(
            SubscriptionAvailability.objects.filter(
                user=self.user,
                make_subscription_available=True
            ).exists()
        )

    def test_multiple_requests_same_user_product(self):
        """Test handling multiple requests from same user for same product."""
        # Create first request
        request1 = SubscriptionRequest.objects.create(
            user=self.user,
            product_name=self.stripe_product.name,
            product_stripe_id=self.stripe_product.id,
            message="First request",
            status='pending'
        )
        
        # Create second request (should be allowed by model)
        request2 = SubscriptionRequest.objects.create(
            user=self.user,
            product_name=self.stripe_product.name,
            product_stripe_id=self.stripe_product.id,
            message="Second request",
            status='pending'
        )
        
        # Approve both requests
        from apps.subscriptions.admin import SubscriptionRequestAdmin
        from django.contrib.admin.sites import AdminSite
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.http import HttpRequest
        
        request = HttpRequest()
        request.user = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="adminpass123"
        )
        request.session = {}
        request._messages = FallbackStorage(request)
        
        admin = SubscriptionRequestAdmin(SubscriptionRequest, AdminSite())
        queryset = SubscriptionRequest.objects.filter(
            user=self.user,
            product_stripe_id=self.stripe_product.id
        )
        
        admin.mark_approved(request, queryset)
        
        # Both requests should be approved
        request1.refresh_from_db()
        request2.refresh_from_db()
        self.assertEqual(request1.status, 'approved')
        self.assertEqual(request2.status, 'approved')
        
        # Only one availability record should exist (update_or_create behavior)
        availability_count = SubscriptionAvailability.objects.filter(
            stripe_product=self.stripe_product,
            user=self.user
        ).count()
        self.assertEqual(availability_count, 1)
        
        # Subscription should be available
        self.assertTrue(is_subscription_available_for_purchase(self.stripe_product.id, self.user))
