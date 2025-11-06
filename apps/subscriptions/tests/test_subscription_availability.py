from django.test import TestCase
from django.contrib.auth import get_user_model
from djstripe.models import Product
from apps.subscriptions.models import SubscriptionAvailability

User = get_user_model()


class SubscriptionAvailabilityModelTests(TestCase):
    """Test cases for the SubscriptionAvailability model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test Stripe product
        self.product = Product.objects.create(
            id='prod_test123',
            name='Test Product',
            active=True
        )
    
    def test_create_global_availability(self):
        """Test creating global subscription availability"""
        availability = SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=None,  # Global availability
            make_subscription_available=True
        )
        
        self.assertEqual(availability.stripe_product, self.product)
        self.assertIsNone(availability.user)
        self.assertTrue(availability.make_subscription_available)
        self.assertEqual(str(availability), "Test Product - Available (Global)")
    
    def test_create_user_specific_availability(self):
        """Test creating user-specific subscription availability"""
        availability = SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=self.user,
            make_subscription_available=True
        )
        
        self.assertEqual(availability.stripe_product, self.product)
        self.assertEqual(availability.user, self.user)
        self.assertTrue(availability.make_subscription_available)
        self.assertEqual(str(availability), f"Test Product - Available (User: {self.user.email})")
    
    def test_unique_together_constraint(self):
        """Test that unique_together constraint works properly"""
        # Create first availability record
        SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=self.user,
            make_subscription_available=True
        )
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            SubscriptionAvailability.objects.create(
                stripe_product=self.product,
                user=self.user,
                make_subscription_available=False
            )
    
    def test_multiple_availabilities_same_product(self):
        """Test that same product can have both global and user-specific availability"""
        global_avail = SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=None,
            make_subscription_available=True
        )
        
        user_avail = SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=self.user,
            make_subscription_available=False
        )
        
        self.assertEqual(SubscriptionAvailability.objects.count(), 2)
        self.assertTrue(global_avail.make_subscription_available)
        self.assertFalse(user_avail.make_subscription_available)
    
    def test_string_representation_request_only(self):
        """Test string representation for request-only availability"""
        availability = SubscriptionAvailability.objects.create(
            stripe_product=self.product,
            user=self.user,
            make_subscription_available=False
        )
        
        expected = f"Test Product - Request Only (User: {self.user.email})"
        self.assertEqual(str(availability), expected)
