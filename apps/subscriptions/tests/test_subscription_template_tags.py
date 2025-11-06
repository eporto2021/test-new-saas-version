from django.test import TestCase
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.utils import timezone
from datetime import timedelta
from djstripe.models import Product, Subscription, SubscriptionItem, Price, Customer, Plan
from djstripe.enums import SubscriptionStatus
from apps.subscriptions.models import SubscriptionAvailability
from apps.subscriptions.templatetags.subscription_tags import (
    user_has_active_subscription_for_product,
    is_subscription_available_for_purchase,
    user_has_requested_subscription,
    user_active_subscriptions
)

User = get_user_model()


class SubscriptionTemplateTagsTests(TestCase):
    """Test cases for subscription template tags"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            id='prod_test123',
            name='Test Product 1',
            active=True
        )
        
        self.product2 = Product.objects.create(
            id='prod_test456',
            name='Test Product 2',
            active=True
        )
        
        # Create customer for user
        self.customer = Customer.objects.create(
            id='cus_test123',
            email=self.user.email
        )
        self.user.customer = self.customer
        self.user.save()
    
    def _create_subscription(self, subscription_id, status, product):
        """Helper method to create a subscription with all required fields"""
        now = timezone.now()
        subscription = Subscription.objects.create(
            id=subscription_id,
            customer=self.customer,
            status=status,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            created=now,
            livemode=False,
            metadata={}
        )
        
        # Create plan, price and subscription item
        plan = Plan.objects.create(
            id=f'plan_{subscription_id}',
            product=product,
            amount=1000,
            currency='usd',
            interval='month',
            active=True
        )
        
        price = Price.objects.create(
            id=f'price_{subscription_id}',
            product=product,
            unit_amount=1000,
            currency='usd',
            active=True
        )
        
        SubscriptionItem.objects.create(
            id=f'si_{subscription_id}',
            subscription=subscription,
            price=price,
            plan_id=plan.djstripe_id,  # Use plan's djstripe_id
            quantity=1
        )
        
        return subscription
    
    def test_user_has_active_subscription_for_product_no_subscription(self):
        """Test template tag when user has no subscription for product"""
        result = user_has_active_subscription_for_product(self.user, self.product1.id)
        self.assertFalse(result)
    
    def test_user_has_active_subscription_for_product_with_subscription(self):
        """Test template tag when user has active subscription for product"""
        self._create_subscription('sub_test123', SubscriptionStatus.active, self.product1)
        
        result = user_has_active_subscription_for_product(self.user, self.product1.id)
        self.assertTrue(result)
    
    def test_user_has_active_subscription_for_product_different_product(self):
        """Test template tag when user has subscription for different product"""
        # Create subscription for product1
        self._create_subscription('sub_test123', SubscriptionStatus.active, self.product1)
        
        # Check for product2 - should return False
        result = user_has_active_subscription_for_product(self.user, self.product2.id)
        self.assertFalse(result)
    
    def test_user_has_active_subscription_for_product_inactive_subscription(self):
        """Test template tag with inactive subscription"""
        self._create_subscription('sub_test123', SubscriptionStatus.canceled, self.product1)
        
        result = user_has_active_subscription_for_product(self.user, self.product1.id)
        self.assertFalse(result)
    
    def test_is_subscription_available_for_purchase_global_true(self):
        """Test global availability when set to True"""
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=None,  # Global
            make_subscription_available=True
        )
        
        result = is_subscription_available_for_purchase(self.product1.id, self.user)
        self.assertTrue(result)
    
    def test_is_subscription_available_for_purchase_global_false(self):
        """Test global availability when set to False"""
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=None,  # Global
            make_subscription_available=False
        )
        
        result = is_subscription_available_for_purchase(self.product1.id, self.user)
        self.assertFalse(result)
    
    def test_is_subscription_available_for_purchase_user_specific_overrides_global(self):
        """Test that user-specific availability overrides global"""
        # Create global availability (False)
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=None,  # Global
            make_subscription_available=False
        )
        
        # Create user-specific availability (True)
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=self.user,
            make_subscription_available=True
        )
        
        result = is_subscription_available_for_purchase(self.product1.id, self.user)
        self.assertTrue(result)  # User-specific should override global
    
    def test_is_subscription_available_for_purchase_no_record_defaults_false(self):
        """Test that missing availability record defaults to False"""
        result = is_subscription_available_for_purchase(self.product1.id, self.user)
        self.assertFalse(result)
    
    def test_user_active_subscriptions_navigation_data(self):
        """Test user_active_subscriptions template tag"""
        self._create_subscription('sub_test123', SubscriptionStatus.active, self.product1)
        
        result = user_active_subscriptions(self.user)
        
        self.assertEqual(len(result), 1)
        nav_item = result[0]
        self.assertEqual(nav_item['name'], 'Test Product 1')
        self.assertEqual(nav_item['slug'], 'test-product-1')
        self.assertEqual(nav_item['icon'], 'fa fa-star')
    
    def test_template_tag_integration(self):
        """Test template tag integration in Django template"""
        # Create availability
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=None,
            make_subscription_available=True
        )
        
        template_content = '''
        {% load subscription_tags %}
        {% user_has_active_subscription_for_product user product.id as has_subscription %}
        {% is_subscription_available_for_purchase product.id user as is_available %}
        Has subscription: {{ has_subscription }}
        Is available: {{ is_available }}
        '''
        
        template = Template(template_content)
        context = Context({
            'user': self.user,
            'product': self.product1
        })
        
        result = template.render(context)
        self.assertIn('Has subscription: False', result)
        self.assertIn('Is available: True', result)
