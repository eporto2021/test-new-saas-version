"""
Simplified test cases for product filtering behavior.

Tests the core requirement: empty ACTIVE_PRODUCTS means no products shown,
not a fallback to all products.
"""
from django.test import TestCase, override_settings
from djstripe.models import Product

from apps.subscriptions.metadata import get_active_products_with_metadata
from apps.subscriptions.exceptions import SubscriptionConfigError


class ProductListFilteringTests(TestCase):
    """Test that product filtering respects ACTIVE_PRODUCTS setting"""
    
    def setUp(self):
        """Create test products"""
        Product.objects.create(
            id='prod_test_1',
            name='Test Product 1',
            active=True
        )
        Product.objects.create(
            id='prod_test_2',
            name='Test Product 2',
            active=True
        )
    
    @override_settings(ACTIVE_PRODUCTS=[])
    def test_empty_list_shows_no_products(self):
        """Core test: empty ACTIVE_PRODUCTS shows nothing, not all products"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        # THIS IS THE KEY BEHAVIOR: Empty list = no products (not all products)
        self.assertEqual(len(products), 0, 
                        "Empty ACTIVE_PRODUCTS should show NO products, not all products")
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_1'])
    def test_only_listed_products_shown(self):
        """Test that only explicitly listed products are shown"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].product.id, 'prod_test_1')
    
    @override_settings(ACTIVE_PRODUCTS=['prod_test_1', 'prod_test_2'])
    def test_all_listed_products_shown(self):
        """Test that all listed products are shown"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        products = list(metadata.get_active_products_with_metadata())
        
        self.assertEqual(len(products), 2)
        product_ids = [p.product.id for p in products]
        self.assertEqual(product_ids, ['prod_test_1', 'prod_test_2'])
    
    @override_settings(ACTIVE_PRODUCTS=['prod_invalid'])
    def test_invalid_product_raises_error(self):
        """Test that invalid product ID raises error"""
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        with self.assertRaises(SubscriptionConfigError) as ctx:
            list(metadata.get_active_products_with_metadata())
        
        self.assertIn('prod_invalid', str(ctx.exception))

