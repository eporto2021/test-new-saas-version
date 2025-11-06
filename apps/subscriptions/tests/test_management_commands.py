from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from django.contrib.auth import get_user_model
from djstripe.models import Product
from apps.subscriptions.models import SubscriptionAvailability

User = get_user_model()


class SubscriptionAvailabilityManagementCommandTests(TestCase):
    """Test cases for subscription availability management commands"""
    
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
    
    def test_setup_subscription_availability_list_empty(self):
        """Test listing availability when no records exist"""
        out = StringIO()
        call_command('setup_subscription_availability', '--list', stdout=out)
        
        output = out.getvalue()
        self.assertIn('No subscription availability records found', output)
    
    def test_setup_subscription_availability_global_default(self):
        """Test setting up global availability with default settings"""
        out = StringIO()
        call_command('setup_subscription_availability', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Setting up global availability', output)
        self.assertIn('Test Product 1 - Request Only (Global)', output)
        self.assertIn('Test Product 2 - Request Only (Global)', output)
        
        # Verify records were created
        availabilities = SubscriptionAvailability.objects.filter(user__isnull=True)
        self.assertEqual(availabilities.count(), 2)
        
        for availability in availabilities:
            self.assertFalse(availability.make_subscription_available)
    
    def test_setup_subscription_availability_global_make_available(self):
        """Test setting up global availability with --make-available flag"""
        out = StringIO()
        call_command('setup_subscription_availability', '--make-available', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Test Product 1 - Available (Global)', output)
        self.assertIn('Test Product 2 - Available (Global)', output)
        
        # Verify records were created with availability set to True
        availabilities = SubscriptionAvailability.objects.filter(user__isnull=True)
        self.assertEqual(availabilities.count(), 2)
        
        for availability in availabilities:
            self.assertTrue(availability.make_subscription_available)
    
    def test_setup_subscription_availability_specific_product(self):
        """Test setting up availability for a specific product"""
        out = StringIO()
        call_command(
            'setup_subscription_availability',
            '--product-id', self.product1.id,
            '--make-available',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('Test Product 1 - Available (Global)', output)
        self.assertNotIn('Test Product 2', output)
        
        # Verify only one record was created
        availabilities = SubscriptionAvailability.objects.filter(user__isnull=True)
        self.assertEqual(availabilities.count(), 1)
        
        availability = availabilities.first()
        self.assertEqual(availability.stripe_product, self.product1)
        self.assertTrue(availability.make_subscription_available)
    
    def test_setup_subscription_availability_user_specific(self):
        """Test setting up user-specific availability"""
        out = StringIO()
        call_command(
            'setup_subscription_availability',
            '--product-id', self.product1.id,
            '--user-id', self.user.id,
            '--make-available',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn(f'Test Product 1 - Available (User: {self.user.email})', output)
        
        # Verify user-specific record was created
        availability = SubscriptionAvailability.objects.get(
            stripe_product=self.product1,
            user=self.user
        )
        self.assertTrue(availability.make_subscription_available)
    
    def test_setup_subscription_availability_invalid_product_id(self):
        """Test command with invalid product ID"""
        with self.assertRaises(CommandError) as cm:
            call_command(
                'setup_subscription_availability',
                '--product-id', 'invalid_product_id'
            )
        
        self.assertIn('Product with ID invalid_product_id not found', str(cm.exception))
    
    def test_setup_subscription_availability_invalid_user_id(self):
        """Test command with invalid user ID"""
        with self.assertRaises(CommandError) as cm:
            call_command(
                'setup_subscription_availability',
                '--product-id', self.product1.id,
                '--user-id', 99999
            )
        
        self.assertIn('User with ID 99999 not found', str(cm.exception))
    
    def test_setup_subscription_availability_list_with_records(self):
        """Test listing availability when records exist"""
        # Create some availability records
        SubscriptionAvailability.objects.create(
            stripe_product=self.product1,
            user=None,
            make_subscription_available=True
        )
        
        SubscriptionAvailability.objects.create(
            stripe_product=self.product2,
            user=self.user,
            make_subscription_available=False
        )
        
        out = StringIO()
        call_command('setup_subscription_availability', '--list', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Current Subscription Availability Settings:', output)
        self.assertIn('Test Product 1 (Global)', output)
        self.assertIn('Available', output)
        self.assertIn(f'Test Product 2 (User: {self.user.email})', output)
        self.assertIn('Request Only', output)
    
    def test_setup_subscription_availability_idempotent(self):
        """Test that running command multiple times is idempotent"""
        # Run command first time
        out1 = StringIO()
        call_command('setup_subscription_availability', stdout=out1)
        
        # Run command second time
        out2 = StringIO()
        call_command('setup_subscription_availability', stdout=out2)
        
        output2 = out2.getvalue()
        self.assertIn('Already exists: Test Product 1 - Request Only (Global)', output2)
        
        # Should still have only 2 records (one per product)
        availabilities = SubscriptionAvailability.objects.filter(user__isnull=True)
        self.assertEqual(availabilities.count(), 2)
