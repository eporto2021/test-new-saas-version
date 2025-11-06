"""
Test cases for ACTIVE_PRODUCTS filtering behavior.

Tests that only products explicitly listed in ACTIVE_PRODUCTS are displayed,
and that empty lists result in no products being shown (not a fallback to all products).
"""
from unittest.mock import patch
from django.test import TestCase, override_settings
from djstripe.models import Product, Price
from djstripe.enums import PriceType, PlanInterval

from apps.subscriptions.metadata import (
    get_active_products_with_metadata,
    ACTIVE_PRODUCTS,
)
from apps.subscriptions.exceptions import SubscriptionConfigError


class ActiveProductsFilteringTests(TestCase):
    """Test that ACTIVE_PRODUCTS filtering works correctly"""
    
    def setUp(self):
        """Create test products in the database"""
        # Create recurring subscription products
        self.product1 = Product.objects.create(
            id='prod_test_sub_1',
            name='Test Subscription 1',
            active=True,
            description='First test subscription'
        )
        
        self.product2 = Product.objects.create(
            id='prod_test_sub_2',
            name='Test Subscription 2',
            active=True,
            description='Second test subscription'
        )
        
        self.product3 = Product.objects.create(
            id='prod_test_sub_3',
            name='Test Subscription 3',
            active=True,
            description='Third test subscription'
        )
        
        # Create prices for the products
        Price.objects.create(
            id='price_test_1_month',
            product=self.product1,
            unit_amount=1000,
            currency='usd',
            active=True,
            type=PriceType.recurring,
            recurring={'interval': PlanInterval.month, 'interval_count': 1}
        )
        
        Price.objects.create(
            id='price_test_2_month',
            product=self.product2,
            unit_amount=2000,
            currency='usd',
            active=True,
            type=PriceType.recurring,
            recurring={'interval': PlanInterval.month, 'interval_count': 1}
        )
    
    @override_settings(ACTIVE_PRODUCTS=[])
    def test_empty_active_products_shows_nothing(self):
        """Test that empty ACTIVE_PRODUCTS list shows no products"""
        # Reload the module to pick up the settings override
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        # Should return empty list, not all products
        self.assertEqual(len(products), 0)
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_sub_1'])
    def test_single_product_in_list(self):
        """Test that only the specified product is returned"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product.id, 'prod_test_sub_1')
        self.assertEqual(products[0].product.name, 'Test Subscription 1')
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_sub_1', 'prod_test_sub_2'])
    def test_multiple_products_in_list(self):
        """Test that all listed products are returned in order"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        self.assertEqual(len(products), 2)
        
        product_ids = [p.product.id for p in products]
        self.assertIn('prod_test_sub_1', product_ids)
        self.assertIn('prod_test_sub_2', product_ids)
        
        # Should maintain order from ACTIVE_PRODUCTS
        self.assertEqual(products[0].product.id, 'prod_test_sub_1')
        self.assertEqual(products[1].product.id, 'prod_test_sub_2')
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_sub_1', 'prod_test_sub_3'])
    def test_only_listed_products_shown(self):
        """Test that unlisted products are not shown"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        # Should have 2 products (not all 3)
        self.assertEqual(len(products), 2)
        
        product_ids = [p.product.id for p in products]
        self.assertIn('prod_test_sub_1', product_ids)
        self.assertIn('prod_test_sub_3', product_ids)
        self.assertNotIn('prod_test_sub_2', product_ids)  # This one is NOT in ACTIVE_PRODUCTS
    
    @override_settings(ACTIVE_PRODUCTS=['prod_nonexistent'])
    def test_nonexistent_product_raises_error(self):
        """Test that listing a non-existent product raises SubscriptionConfigError"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        with self.assertRaises(SubscriptionConfigError) as context:
            list(metadata.get_active_products_with_metadata())
        
        self.assertIn('prod_nonexistent', str(context.exception))
        self.assertIn('found in database', str(context.exception))
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_sub_1', 'prod_nonexistent'])
    def test_mix_of_valid_and_invalid_products(self):
        """Test that having one invalid product raises error (doesn't return partial results)"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        with self.assertRaises(SubscriptionConfigError) as context:
            list(metadata.get_active_products_with_metadata())
        
        self.assertIn('prod_nonexistent', str(context.exception))
    
    def test_product_metadata_extraction(self):
        """Test that product metadata is correctly extracted"""
        from importlib import reload
        from apps.subscriptions import metadata
        
        # Set ACTIVE_PRODUCTS via settings override
        with self.settings(ACTIVE_PRODUCTS=['prod_test_sub_1']):
            reload(metadata)
            products = list(metadata.get_active_products_with_metadata())
            
            self.assertEqual(len(products), 1)
            product_with_meta = products[0]
            
            # Check product
            self.assertEqual(product_with_meta.product.id, 'prod_test_sub_1')
            
            # Check metadata
            self.assertEqual(product_with_meta.metadata.stripe_id, 'prod_test_sub_1')
            self.assertEqual(product_with_meta.metadata.name, 'Test Subscription 1')
            self.assertEqual(product_with_meta.metadata.description, 'First test subscription')
            self.assertEqual(product_with_meta.metadata.slug, 'test-subscription-1')
    
    def test_price_displays_in_metadata(self):
        """Test that price displays are correctly populated in metadata"""
        from importlib import reload
        from apps.subscriptions import metadata
        
        with self.settings(ACTIVE_PRODUCTS=['prod_test_sub_1']):
            reload(metadata)
            products = list(metadata.get_active_products_with_metadata())
            
            product_with_meta = products[0]
            
            # Should have price display for monthly interval
            self.assertIn('month', product_with_meta.metadata.price_displays)
            price_display = product_with_meta.metadata.price_displays['month']
            
            # Should be a string (not 'Unknown')
            self.assertIsInstance(price_display, str)
            self.assertNotEqual(price_display, 'Unknown')


class ProductOrderingTests(TestCase):
    """Test that products are returned in the order specified in ACTIVE_PRODUCTS"""
    
    def setUp(self):
        """Create test products"""
        self.products = []
        for i in range(1, 6):
            product = Product.objects.create(
                id=f'prod_order_{i}',
                name=f'Product {i}',
                active=True
            )
            self.products.append(product)
    
    @override_settings(ACTIVE_PRODUCTS=['prod_order_3', 'prod_order_1', 'prod_order_5'])
    def test_products_returned_in_list_order(self):
        """Test that products are returned in the exact order of ACTIVE_PRODUCTS"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        self.assertEqual(len(products), 3)
        
        # Check order matches ACTIVE_PRODUCTS list
        self.assertEqual(products[0].product.id, 'prod_order_3')
        self.assertEqual(products[1].product.id, 'prod_order_1')
        self.assertEqual(products[2].product.id, 'prod_order_5')


class ActiveProductIDsSetTests(TestCase):
    """Test that ACTIVE_PRODUCT_IDS set is correctly generated"""
    
    @override_settings(ACTIVE_PRODUCTS=['prod_1', 'prod_2', 'prod_3'])
    def test_active_product_ids_set_created(self):
        """Test that ACTIVE_PRODUCT_IDS set matches ACTIVE_PRODUCTS list"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        # ACTIVE_PRODUCT_IDS should be a set
        self.assertIsInstance(metadata.ACTIVE_PRODUCT_IDS, set)
        
        # Should contain all IDs from ACTIVE_PRODUCTS
        self.assertEqual(metadata.ACTIVE_PRODUCT_IDS, {'prod_1', 'prod_2', 'prod_3'})
    
    @override_settings(ACTIVE_PRODUCTS=[])
    def test_empty_active_products_creates_empty_set(self):
        """Test that empty ACTIVE_PRODUCTS results in empty set"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        self.assertEqual(metadata.ACTIVE_PRODUCT_IDS, set())
        self.assertEqual(len(metadata.ACTIVE_PRODUCT_IDS), 0)

