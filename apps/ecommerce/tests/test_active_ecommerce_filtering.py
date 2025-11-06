"""
Test cases for ACTIVE_ECOMMERCE_PRODUCT_IDS filtering behavior.

Tests that bootstrap_ecommerce command only creates ProductConfiguration entries
for products explicitly listed in ACTIVE_ECOMMERCE_PRODUCT_IDS, and that empty
lists result in all ProductConfigurations being deactivated.
"""
from io import StringIO
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.management import call_command
from djstripe.models import Product, Price
from djstripe.enums import PriceType

from apps.ecommerce.models import ProductConfiguration


class BootstrapEcommerceFilteringTests(TestCase):
    """Test that bootstrap_ecommerce respects ACTIVE_ECOMMERCE_PRODUCT_IDS"""
    
    def setUp(self):
        """Create test products in the database"""
        # Create one-time purchase products
        self.ecom_product1 = Product.objects.create(
            id='prod_ecom_1',
            name='One-time Product 1',
            active=True,
            description='First one-time product'
        )
        
        self.ecom_product2 = Product.objects.create(
            id='prod_ecom_2',
            name='One-time Product 2',
            active=True,
            description='Second one-time product'
        )
        
        self.ecom_product3 = Product.objects.create(
            id='prod_ecom_3',
            name='One-time Product 3',
            active=True,
            description='Third one-time product'
        )
        
        # Create prices (one-time)
        self.price1 = Price.objects.create(
            id='price_ecom_1',
            product=self.ecom_product1,
            unit_amount=5000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        self.ecom_product1.default_price = self.price1
        self.ecom_product1.save()
        
        self.price2 = Price.objects.create(
            id='price_ecom_2',
            product=self.ecom_product2,
            unit_amount=10000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        self.ecom_product2.default_price = self.price2
        self.ecom_product2.save()
        
        self.price3 = Price.objects.create(
            id='price_ecom_3',
            product=self.ecom_product3,
            unit_amount=15000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        self.ecom_product3.default_price = self.price3
        self.ecom_product3.save()
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=[])
    def test_empty_list_deactivates_all_products(self, mock_call_command, mock_create_keys):
        """Test that empty ACTIVE_ECOMMERCE_PRODUCT_IDS deactivates all ProductConfigurations"""
        mock_create_keys.return_value = False
        
        # Create some existing active ProductConfigurations
        ProductConfiguration.objects.create(
            product=self.ecom_product1,
            slug='one-time-product-1',
            is_active=True,
            overview='Test'
        )
        ProductConfiguration.objects.create(
            product=self.ecom_product2,
            slug='one-time-product-2',
            is_active=True,
            overview='Test'
        )
        
        # Run bootstrap_ecommerce
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # All ProductConfigurations should be deactivated
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        self.assertEqual(active_configs.count(), 0)
        
        # All configs should exist but be inactive
        all_configs = ProductConfiguration.objects.all()
        self.assertEqual(all_configs.count(), 2)
        for config in all_configs:
            self.assertFalse(config.is_active)
        
        # Check output message
        output = out.getvalue()
        self.assertIn('ACTIVE_ECOMMERCE_PRODUCT_IDS is empty', output)
        self.assertIn('Deactivating', output)
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_ecom_1'])
    def test_single_product_in_list(self, mock_call_command, mock_create_keys):
        """Test that only the specified product gets an active ProductConfiguration"""
        mock_create_keys.return_value = False
        
        # Run bootstrap_ecommerce
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # Should have 1 active ProductConfiguration
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        self.assertEqual(active_configs.count(), 1)
        self.assertEqual(active_configs.first().product.id, 'prod_ecom_1')
        
        # Check output
        output = out.getvalue()
        self.assertIn('Creating product configurations for 1 products', output)
        self.assertIn('One-time Product 1', output)
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_ecom_1', 'prod_ecom_3'])
    def test_multiple_products_in_list(self, mock_call_command, mock_create_keys):
        """Test that all listed products get active ProductConfigurations"""
        mock_create_keys.return_value = False
        
        # Run bootstrap_ecommerce
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # Should have 2 active ProductConfigurations
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        self.assertEqual(active_configs.count(), 2)
        
        product_ids = [config.product.id for config in active_configs]
        self.assertIn('prod_ecom_1', product_ids)
        self.assertIn('prod_ecom_3', product_ids)
        self.assertNotIn('prod_ecom_2', product_ids)
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_ecom_2'])
    def test_deactivates_products_not_in_list(self, mock_call_command, mock_create_keys):
        """Test that products not in the list get deactivated"""
        mock_create_keys.return_value = False
        
        # Create ProductConfigurations for all products (all active)
        ProductConfiguration.objects.create(
            product=self.ecom_product1,
            slug='one-time-product-1',
            is_active=True,
            overview='Test'
        )
        ProductConfiguration.objects.create(
            product=self.ecom_product2,
            slug='one-time-product-2',
            is_active=True,
            overview='Test'
        )
        ProductConfiguration.objects.create(
            product=self.ecom_product3,
            slug='one-time-product-3',
            is_active=True,
            overview='Test'
        )
        
        # Run bootstrap_ecommerce with only prod_ecom_2
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # Only prod_ecom_2 should be active
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        self.assertEqual(active_configs.count(), 1)
        self.assertEqual(active_configs.first().product.id, 'prod_ecom_2')
        
        # Others should be deactivated
        inactive_configs = ProductConfiguration.objects.filter(is_active=False)
        self.assertEqual(inactive_configs.count(), 2)
        
        inactive_ids = [config.product.id for config in inactive_configs]
        self.assertIn('prod_ecom_1', inactive_ids)
        self.assertIn('prod_ecom_3', inactive_ids)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Deactivating 2 product(s)', output)
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_ecom_1'])
    def test_reactivates_previously_deactivated_product(self, mock_call_command, mock_create_keys):
        """Test that running bootstrap again reactivates a product that was in the list"""
        mock_create_keys.return_value = False
        
        # Create a deactivated ProductConfiguration
        config = ProductConfiguration.objects.create(
            product=self.ecom_product1,
            slug='one-time-product-1',
            is_active=False,
            overview='Test'
        )
        
        # Run bootstrap_ecommerce
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # Refresh from database
        config.refresh_from_db()
        
        # Should now be active
        self.assertTrue(config.is_active)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Activated product configuration', output)
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_nonexistent'])
    def test_nonexistent_product_warning(self, mock_call_command, mock_create_keys):
        """Test that listing a non-existent product shows a warning"""
        mock_create_keys.return_value = False
        
        # Run bootstrap_ecommerce
        out = StringIO()
        call_command('bootstrap_ecommerce', stdout=out)
        
        # Should show warning
        output = out.getvalue()
        self.assertIn('Warning: Product prod_nonexistent not found', output)
        
        # No ProductConfigurations should be created
        self.assertEqual(ProductConfiguration.objects.count(), 0)


class EcommerceViewFilteringTests(TestCase):
    """Test that ecommerce views only show active ProductConfigurations"""
    
    def setUp(self):
        """Create test data"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            id='prod_view_1',
            name='View Product 1',
            active=True
        )
        
        self.product2 = Product.objects.create(
            id='prod_view_2',
            name='View Product 2',
            active=True
        )
        
        # Create prices
        price1 = Price.objects.create(
            id='price_view_1',
            product=self.product1,
            unit_amount=5000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        self.product1.default_price = price1
        self.product1.save()
        
        price2 = Price.objects.create(
            id='price_view_2',
            product=self.product2,
            unit_amount=10000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        self.product2.default_price = price2
        self.product2.save()
        
        # Create ProductConfigurations (one active, one inactive)
        self.config1 = ProductConfiguration.objects.create(
            product=self.product1,
            slug='view-product-1',
            is_active=True,
            overview='Active product'
        )
        
        self.config2 = ProductConfiguration.objects.create(
            product=self.product2,
            slug='view-product-2',
            is_active=False,
            overview='Inactive product'
        )
    
    def test_ecommerce_home_only_shows_active_configs(self):
        """Test that ecommerce_home view only returns active ProductConfigurations"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/ecommerce/')
        
        # Should only include active product
        products = response.context['products']
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().product.id, 'prod_view_1')
    
    def test_inactive_configs_not_accessible(self):
        """Test that inactive ProductConfigurations are filtered out"""
        from apps.ecommerce.models import ProductConfiguration
        
        active_configs = ProductConfiguration.objects.filter(is_active=True)
        self.assertEqual(active_configs.count(), 1)
        
        inactive_configs = ProductConfiguration.objects.filter(is_active=False)
        self.assertEqual(inactive_configs.count(), 1)


class ProductConfigurationSlugTests(TestCase):
    """Test that slugs are correctly generated from product names"""
    
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.create_stripe_api_keys_if_necessary')
    @patch('apps.ecommerce.management.commands.bootstrap_ecommerce.call_command')
    @override_settings(ACTIVE_ECOMMERCE_PRODUCT_IDS=['prod_slug_test'])
    def test_slug_generation(self, mock_call_command, mock_create_keys):
        """Test that slugs are properly generated from product names"""
        mock_create_keys.return_value = False
        
        # Create product with special characters
        product = Product.objects.create(
            id='prod_slug_test',
            name='My Amazing Product! (2024)',
            active=True
        )
        
        price = Price.objects.create(
            id='price_slug_test',
            product=product,
            unit_amount=5000,
            currency='usd',
            active=True,
            type=PriceType.one_time
        )
        product.default_price = price
        product.save()
        
        # Run bootstrap_ecommerce
        call_command('bootstrap_ecommerce', stdout=StringIO())
        
        # Check that slug was generated correctly
        config = ProductConfiguration.objects.get(product=product)
        self.assertEqual(config.slug, 'my-amazing-product-2024')

