"""
Management command to add a product to ACTIVE_PRODUCTS in settings files.

Usage:
    python manage.py add_active_product prod_ABC123 --env development
    python manage.py add_active_product prod_ABC123 --env production
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from djstripe.models import Product


class Command(BaseCommand):
    help = 'Add a Stripe product to ACTIVE_PRODUCTS in settings.py or settings_production.py'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='Stripe product ID (e.g., prod_ABC123)'
        )
        parser.add_argument(
            '--env',
            type=str,
            choices=['development', 'production', 'dev', 'prod'],
            default='development',
            help='Target environment: development or production'
        )
        parser.add_argument(
            '--default',
            action='store_true',
            help='Set this product as the default (is_default=True)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        env = options['env']
        is_default = options['default']
        
        # Normalize environment name
        if env in ['dev', 'development']:
            env = 'development'
            settings_file = 'test/settings.py'
        else:
            env = 'production'
            settings_file = 'test/settings_production.py'
        
        # Get the product from Stripe
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise CommandError(
                f'Product {product_id} not found in database. '
                f'Run "python manage.py djstripe_sync_models Product" first.'
            )
        
        self.stdout.write(f'\nProduct found: {product.name}')
        self.stdout.write(f'Description: {product.description or "No description"}')
        self.stdout.write(f'Active: {product.active}')
        
        if not product.active:
            self.stdout.write(self.style.WARNING('Warning: This product is not active in Stripe'))
        
        # Generate the ProductMetadata code
        product_metadata_code = self._generate_product_metadata(product, is_default)
        
        # Update the settings file
        self._update_settings_file(settings_file, product_metadata_code, product_id, env)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully added {product.name} to {settings_file}'))
        self.stdout.write(self.style.SUCCESS(f'   Environment: {env}'))
        self.stdout.write(self.style.SUCCESS(f'   Product ID: {product_id}'))
        
        if is_default:
            self.stdout.write(self.style.SUCCESS(f'   Set as default: Yes'))

    def _generate_product_metadata(self, product, is_default):
        """Generate ProductMetadata code for the product"""
        from django.utils.text import slugify
        
        slug = slugify(product.name)
        
        # Get features from product metadata or use defaults
        features = []
        if product.metadata and 'features' in product.metadata:
            features = product.metadata['features']
        else:
            features = ['Full access to all features', 'Priority support', '24/7 availability']
        
        # Format features list
        features_str = ',\n            '.join([f"'{f}'" for f in features])
        
        code = f"""    ProductMetadata(
        stripe_id='{product.id}',
        slug='{slug}',
        name='{product.name}',
        features=[
            {features_str}
        ],
        price_displays={{}},
        description='{product.description or f"The {product.name} plan"}',
        is_default={is_default}
    ),"""
        
        return code

    def _update_settings_file(self, settings_file, product_metadata_code, product_id, env):
        """Update the settings file with the new product"""
        file_path = Path(settings_file)
        
        if not file_path.exists():
            raise CommandError(f'Settings file not found: {settings_file}')
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if product already exists
        if product_id in content:
            self.stdout.write(self.style.WARNING(f'\nProduct {product_id} already exists in {settings_file}'))
            response = input('Do you want to update it? (yes/no): ')
            if response.lower() not in ['yes', 'y']:
                self.stdout.write('Cancelled.')
                return
            
            # Remove existing entry
            content = self._remove_existing_product(content, product_id)
        
        # Find ACTIVE_PRODUCTS list
        if 'ACTIVE_PRODUCTS = [' in content:
            # Add to existing list
            content = self._add_to_active_products(content, product_metadata_code)
        else:
            # Create new ACTIVE_PRODUCTS list
            if env == 'production':
                content = self._create_active_products_section_production(content, product_metadata_code)
            else:
                content = self._create_active_products_section_development(content, product_metadata_code)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)

    def _remove_existing_product(self, content, product_id):
        """Remove existing product entry from ACTIVE_PRODUCTS"""
        # Pattern to match ProductMetadata entry
        pattern = rf"ProductMetadata\(\s*stripe_id='{product_id}'.*?\),\n"
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)
        return content

    def _add_to_active_products(self, content, product_metadata_code):
        """Add product to existing ACTIVE_PRODUCTS list"""
        # Find the closing bracket of ACTIVE_PRODUCTS
        pattern = r'(ACTIVE_PRODUCTS = \[.*?)(^\])'
        
        def replacer(match):
            existing = match.group(1)
            closing = match.group(2)
            
            # Add new product before closing bracket
            return f"{existing}\n{product_metadata_code}\n{closing}"
        
        content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
        return content

    def _create_active_products_section_development(self, content, product_metadata_code):
        """Create ACTIVE_PRODUCTS section in settings.py"""
        # Find a good place to insert (after ACTIVE_PLAN_INTERVALS)
        insert_after = 'ACTIVE_PLAN_INTERVALS = ['
        
        if insert_after in content:
            # Find the end of ACTIVE_PLAN_INTERVALS
            pattern = r'(ACTIVE_PLAN_INTERVALS = \[.*?\]\n)'
            
            def replacer(match):
                existing = match.group(1)
                new_section = f"""ACTIVE_PRODUCTS = [
{product_metadata_code}
]

"""
                return f"{existing}{new_section}"
            
            content = re.sub(pattern, replacer, content, flags=re.DOTALL)
        
        return content

    def _create_active_products_section_production(self, content, product_metadata_code):
        """Create ACTIVE_PRODUCTS section in settings_production.py"""
        # Add after imports
        insert_text = f"""
# Production-specific subscription products
from apps.subscriptions.metadata import ProductMetadata

ACTIVE_PRODUCTS = [
{product_metadata_code}
]

"""
        
        # Find a good place to insert (after STRIPE_LIVE_MODE)
        if 'STRIPE_LIVE_MODE' in content:
            pattern = r'(STRIPE_LIVE_MODE = .*?\n)'
            
            def replacer(match):
                return f"{match.group(1)}{insert_text}"
            
            content = re.sub(pattern, replacer, content)
        else:
            # Add at the end
            content += insert_text
        
        return content
