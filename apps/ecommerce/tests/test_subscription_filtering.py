from django.test import TestCase
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.utils import timezone
from datetime import timedelta
from djstripe.models import Product, Subscription, SubscriptionItem, Price, Customer, Plan
from djstripe.enums import SubscriptionStatus
from apps.subscriptions.metadata import ProductMetadata, ProductWithMetadata
from apps.subscriptions.templatetags.subscription_tags import user_has_active_subscription_for_product

User = get_user_model()


class SubscriptionFilteringTests(TestCase):
    """Test cases for subscription filtering in ecommerce templates"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create customer for user
        self.customer = Customer.objects.create(
            id='cus_test123',
            email=self.user.email
        )
        self.user.customer = self.customer
        self.user.save()
        
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
        
        # Create product metadata
        self.metadata1 = ProductMetadata(
            stripe_id=self.product1.id,
            slug='test-product-1',
            name='Test Product 1',
            features=['Feature 1', 'Feature 2'],
            description='Test product 1 description'
        )
        
        self.metadata2 = ProductMetadata(
            stripe_id=self.product2.id,
            slug='test-product-2',
            name='Test Product 2',
            features=['Feature 3', 'Feature 4'],
            description='Test product 2 description'
        )
        
        # Create product with metadata objects
        self.product_with_metadata1 = ProductWithMetadata(
            product=self.product1,
            metadata=self.metadata1
        )
        
        self.product_with_metadata2 = ProductWithMetadata(
            product=self.product2,
            metadata=self.metadata2
        )
    
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
    
    def test_template_filtering_no_subscriptions(self):
        """Test template filtering when user has no subscriptions"""
        subscription_products = [self.product_with_metadata1, self.product_with_metadata2]
        
        template_content = '''
        {% load subscription_tags %}
        {% for product in subscription_products %}
          {% user_has_active_subscription_for_product user product.product.id as has_subscription %}
          {% if not has_subscription %}
            SHOW: {{ product.metadata.name }}
          {% else %}
            HIDE: {{ product.metadata.name }}
          {% endif %}
        {% endfor %}
        '''
        
        template = Template(template_content)
        context = Context({
            'user': self.user,
            'subscription_products': subscription_products
        })
        
        result = template.render(context)
        
        # Both products should show
        self.assertIn('SHOW: Test Product 1', result)
        self.assertIn('SHOW: Test Product 2', result)
        self.assertNotIn('HIDE:', result)
    
    def test_template_filtering_with_subscription(self):
        """Test template filtering when user has subscription for one product"""
        # Create subscription for product1
        self._create_subscription('sub_test123', SubscriptionStatus.active, self.product1)
        
        subscription_products = [self.product_with_metadata1, self.product_with_metadata2]
        
        template_content = '''
        {% load subscription_tags %}
        {% for product in subscription_products %}
          {% user_has_active_subscription_for_product user product.product.id as has_subscription %}
          {% if not has_subscription %}
            SHOW: {{ product.metadata.name }}
          {% else %}
            HIDE: {{ product.metadata.name }}
          {% endif %}
        {% endfor %}
        '''
        
        template = Template(template_content)
        context = Context({
            'user': self.user,
            'subscription_products': subscription_products
        })
        
        result = template.render(context)
        
        # Product1 should be hidden, Product2 should show
        self.assertIn('HIDE: Test Product 1', result)
        self.assertIn('SHOW: Test Product 2', result)
    
    def test_template_filtering_all_subscribed(self):
        """Test template filtering when user has subscriptions for all products"""
        # Create subscriptions for both products
        self._create_subscription('sub_test123', SubscriptionStatus.active, self.product1)
        self._create_subscription('sub_test456', SubscriptionStatus.active, self.product2)
        
        subscription_products = [self.product_with_metadata1, self.product_with_metadata2]
        
        template_content = '''
        {% load subscription_tags %}
        {% for product in subscription_products %}
          {% user_has_active_subscription_for_product user product.product.id as has_subscription %}
          {% if not has_subscription %}
            SHOW: {{ product.metadata.name }}
          {% else %}
            HIDE: {{ product.metadata.name }}
          {% endif %}
        {% endfor %}
        '''
        
        template = Template(template_content)
        context = Context({
            'user': self.user,
            'subscription_products': subscription_products
        })
        
        result = template.render(context)
        
        # Both products should be hidden
        self.assertIn('HIDE: Test Product 1', result)
        self.assertIn('HIDE: Test Product 2', result)
        self.assertNotIn('SHOW:', result)
    
    def test_subscription_statuses_filtering(self):
        """Test filtering with different subscription statuses"""
        subscription_statuses = [
            SubscriptionStatus.active,
            SubscriptionStatus.trialing,
            SubscriptionStatus.past_due
        ]
        
        for i, status in enumerate(subscription_statuses):
            subscription = self._create_subscription(f'sub_test{i}', status, self.product1)
            
            # All these statuses should result in hiding the product
            result = user_has_active_subscription_for_product(self.user, self.product1.id)
            self.assertTrue(result, f"Status {status} should be considered active")
            
            # Clean up for next iteration
            subscription.delete()
    
    def test_inactive_subscription_statuses(self):
        """Test that inactive subscription statuses don't hide products"""
        inactive_statuses = [
            SubscriptionStatus.canceled,
            SubscriptionStatus.incomplete,
            SubscriptionStatus.incomplete_expired,
            SubscriptionStatus.unpaid
        ]
        
        for i, status in enumerate(inactive_statuses):
            subscription = self._create_subscription(f'sub_test{i}', status, self.product1)
            
            # Inactive statuses should not hide the product
            result = user_has_active_subscription_for_product(self.user, self.product1.id)
            self.assertFalse(result, f"Status {status} should not be considered active")
            
            # Clean up for next iteration
            subscription.delete()
