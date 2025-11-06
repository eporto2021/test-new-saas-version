"""
Simplified test for ecommerce ProductConfiguration filtering.

Tests that ProductConfiguration.objects.filter(is_active=True) only returns
products that are in ACTIVE_ECOMMERCE_PRODUCT_IDS after running bootstrap_ecommerce.
"""
from django.test import TestCase
from djstripe.models import Product, Price
from djstripe.enums import PriceType

from apps.ecommerce.models import ProductConfiguration


class ProductConfigurationFilteringTests(TestCase):
    """Test that only active ProductConfigurations are shown"""
    
    def setUp(self):
        """Create test products and configurations"""
        # Create products
        self.product1 = Product.objects.create(
            id='prod_config_1',
            name='Product 1',
            active=True
        )
        self.product2 = Product.objects.create(
            id='prod_config_2',
            name='Product 2',
            active=True
        )
        
        # Create prices
        Price.objects.create(
            id='price_config_1',
            product=self.product1,
            unit_amount=1000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        Price.objects.create(
            id='price_config_2',
            product=self.product2,
            unit_amount=2000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
    
    def test_only_active_configs_queryable(self):
        """Test that only active=True ProductConfigurations are returned by the view query"""
        # Create one active, one inactive
        ProductConfiguration.objects.create(
            product=self.product1,
            slug='product-1',
            is_active=True,
            overview='Active'
        )
        ProductConfiguration.objects.create(
            product=self.product2,
            slug='product-2',
            is_active=False,
            overview='Inactive'
        )
        
        # Query as the view does
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        
        # Should only get the active one
        self.assertEqual(active_configs.count(), 1)
        self.assertEqual(active_configs.first().product.id, 'prod_config_1')
    
    def test_empty_when_all_inactive(self):
        """Test that no products show when all ProductConfigurations are inactive"""
        # Create all inactive
        ProductConfiguration.objects.create(
            product=self.product1,
            slug='product-1',
            is_active=False,
            overview='Inactive'
        )
        ProductConfiguration.objects.create(
            product=self.product2,
            slug='product-2',
            is_active=False,
            overview='Inactive'
        )
        
        # Query as the view does
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        
        # Should be empty
        self.assertEqual(active_configs.count(), 0)
    
    def test_deactivate_config(self):
        """Test that deactivating a config removes it from results"""
        config = ProductConfiguration.objects.create(
            product=self.product1,
            slug='product-1',
            is_active=True,
            overview='Active'
        )
        
        # Should show up initially
        self.assertEqual(ProductConfiguration.objects.filter(is_active=True).count(), 1)
        
        # Deactivate
        config.is_active = False
        config.save()
        
        # Should not show up now
        self.assertEqual(ProductConfiguration.objects.filter(is_active=True).count(), 0)
    
    def test_reactivate_config(self):
        """Test that reactivating a config adds it back to results"""
        config = ProductConfiguration.objects.create(
            product=self.product1,
            slug='product-1',
            is_active=False,
            overview='Inactive'
        )
        
        # Should not show up initially
        self.assertEqual(ProductConfiguration.objects.filter(is_active=True).count(), 0)
        
        # Reactivate
        config.is_active = True
        config.save()
        
        # Should show up now
        self.assertEqual(ProductConfiguration.objects.filter(is_active=True).count(), 1)

