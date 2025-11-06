from django.test import TestCase
from django.contrib.auth import get_user_model
from django.template import Template, Context
from djstripe.models import Product, Subscription, SubscriptionItem, Price, Customer
from djstripe.enums import SubscriptionStatus
from apps.services.models import Service, UserServiceAccess
from apps.services.templatetags.services_tags import user_navigation_items

User = get_user_model()


class NavigationDeduplicationTests(TestCase):
    """Test cases for navigation deduplication logic"""
    
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
        
        # Create test services
        self.service1 = Service.objects.create(
            name='Test Service 1',
            slug='test-service-1',
            stripe_product=self.product1,
            icon='fa fa-cube'
        )
        
        self.service2 = Service.objects.create(
            name='Test Service 2',
            slug='test-service-2',
            stripe_product=self.product2,
            icon='fa fa-star'
        )
    
    def test_navigation_items_service_only(self):
        """Test navigation when user has service access but no subscription"""
        # Grant service access
        UserServiceAccess.objects.create(
            user=self.user,
            service=self.service1,
            is_active=True
        )
        
        nav_items = user_navigation_items(self.user)
        
        self.assertEqual(len(nav_items), 1)
        item = nav_items[0]
        self.assertEqual(item['name'], 'Test Service 1')
        self.assertEqual(item['type'], 'service')
        self.assertIn('services/test-service-1', item['url'])
    
    def test_navigation_items_subscription_only(self):
        """Test navigation when user has subscription but no service access"""
        # Create subscription without corresponding service
        subscription = Subscription.objects.create(
            id='sub_test123',
            customer=self.customer,
            status=SubscriptionStatus.active
        )
        
        price = Price.objects.create(
            id='price_test123',
            product=self.product1,
            unit_amount=1000,
            currency='usd'
        )
        
        SubscriptionItem.objects.create(
            id='si_test123',
            subscription=subscription,
            price=price,
            quantity=1
        )
        
        nav_items = user_navigation_items(self.user)
        
        self.assertEqual(len(nav_items), 1)
        item = nav_items[0]
        self.assertEqual(item['name'], 'Test Product 1')
        self.assertEqual(item['type'], 'subscription')
        self.assertIn('subscriptions/service/test-product-1', item['url'])
    
    def test_navigation_items_deduplication_service_priority(self):
        """Test that service takes priority over subscription when both exist"""
        # Grant service access
        UserServiceAccess.objects.create(
            user=self.user,
            service=self.service1,
            is_active=True
        )
        
        # Create subscription for same product
        subscription = Subscription.objects.create(
            id='sub_test123',
            customer=self.customer,
            status=SubscriptionStatus.active
        )
        
        price = Price.objects.create(
            id='price_test123',
            product=self.product1,
            unit_amount=1000,
            currency='usd'
        )
        
        SubscriptionItem.objects.create(
            id='si_test123',
            subscription=subscription,
            price=price,
            quantity=1
        )
        
        nav_items = user_navigation_items(self.user)
        
        # Should only show service, not subscription (deduplication)
        self.assertEqual(len(nav_items), 1)
        item = nav_items[0]
        self.assertEqual(item['name'], 'Test Service 1')
        self.assertEqual(item['type'], 'service')
        self.assertIn('services/test-service-1', item['url'])
    
    def test_navigation_items_mixed_scenarios(self):
        """Test navigation with mixed service and subscription scenarios"""
        # Grant access to service1
        UserServiceAccess.objects.create(
            user=self.user,
            service=self.service1,
            is_active=True
        )
        
        # Create subscription for product2 (no corresponding service)
        subscription = Subscription.objects.create(
            id='sub_test123',
            customer=self.customer,
            status=SubscriptionStatus.active
        )
        
        price = Price.objects.create(
            id='price_test123',
            product=self.product2,
            unit_amount=1000,
            currency='usd'
        )
        
        SubscriptionItem.objects.create(
            id='si_test123',
            subscription=subscription,
            price=price,
            quantity=1
        )
        
        nav_items = user_navigation_items(self.user)
        
        # Should show both: service1 and subscription for product2
        self.assertEqual(len(nav_items), 2)
        
        # Find items by type
        service_item = next(item for item in nav_items if item['type'] == 'service')
        subscription_item = next(item for item in nav_items if item['type'] == 'subscription')
        
        self.assertEqual(service_item['name'], 'Test Service 1')
        self.assertEqual(subscription_item['name'], 'Test Product 2')
    
    def test_navigation_items_no_access(self):
        """Test navigation when user has no access to anything"""
        nav_items = user_navigation_items(self.user)
        self.assertEqual(len(nav_items), 0)
    
    def test_navigation_items_anonymous_user(self):
        """Test navigation for anonymous user"""
        anonymous_user = User()
        nav_items = user_navigation_items(anonymous_user)
        self.assertEqual(len(nav_items), 0)
    
    def test_template_integration(self):
        """Test navigation template tag integration"""
        # Grant service access
        UserServiceAccess.objects.create(
            user=self.user,
            service=self.service1,
            is_active=True
        )
        
        template_content = '''
        {% load services_tags %}
        {% user_navigation_items user as navigation_items %}
        {% for item in navigation_items %}
          {{ item.name }} ({{ item.type }}) -> {{ item.url }}
        {% endfor %}
        '''
        
        template = Template(template_content)
        context = Context({'user': self.user})
        result = template.render(context)
        
        self.assertIn('Test Service 1 (service)', result)
        self.assertIn('services/test-service-1', result)
