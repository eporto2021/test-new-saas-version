"""
Management command to add/remove products from available subscriptions.

Manages the ACTIVE_PRODUCTS list in metadata.py (simple list of product IDs).

Usage:
    python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT
    python manage.py update_available_subscriptions production prod_T9Fmx6Ey5TNwLT --remove
    python manage.py update_available_subscriptions list
"""

import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from djstripe.models import Product


class Command(BaseCommand):
    help = 'Add or remove products from ACTIVE_PRODUCTS list in metadata.py'

    def add_arguments(self, parser):
        parser.add_argument(
            'environment',
            type=str,
            choices=['development', 'production', 'dev', 'prod', 'list'],
            help='Environment (dev/prod) or "list" to show current'
        )
        parser.add_argument(
            'product_id',
            type=str,
            nargs='?',
            help='Stripe product ID (e.g., prod_T9Fmx6Ey5TNwLT)'
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove product instead of adding'
        )

    def handle(self, *args, **options):
        env = options['environment']
        product_id = options.get('product_id')
        remove = options.get('remove', False)

        if env == 'list':
            self._list_available_products()
            return

        if not product_id:
            self.stdout.write(self.style.ERROR('Product ID is required (unless using "list")'))
            return

        # Normalize environment
        if env in ['dev', 'development']:
            env = 'development'
            target_file = 'apps/subscriptions/metadata.py'
        else:
            env = 'production'
            target_file = 'test/settings_production.py'

        try:
            product = Product.objects.get(id=product_id)
            product_name = product.name
        except (Product.DoesNotExist, Exception):
            # Try to get product info from Stripe API
            try:
                import stripe
                stripe.api_key = settings.STRIPE_TEST_SECRET_KEY if not settings.STRIPE_LIVE_MODE else settings.STRIPE_LIVE_SECRET_KEY
                stripe_product = stripe.Product.retrieve(product_id)
                product_name = stripe_product.name
                self.stdout.write(f'ℹ️  Product {product_name} not in database, using Stripe API data')
            except Exception as e:
                # If running locally and product not found, use a placeholder name
                if not settings.STRIPE_LIVE_MODE:
                    product_name = f"Product {product_id}"
                    self.stdout.write(f'⚠️  Product {product_id} not found in test environment, using placeholder name')
                    self.stdout.write(f'   This will be validated in production with live Stripe keys')
                else:
                    self.stdout.write(self.style.ERROR(f'Product {product_id} not found in database or Stripe: {str(e)}'))
                    return
        
        if remove:
            self._remove_product_from_list(product_id, product_name, target_file)
        else:
            self._add_product_to_list(product_id, product_name, target_file)

    def _add_product_to_list(self, product_id, product_name, target_file):
        """Add product ID to ACTIVE_PRODUCTS list"""
        self.stdout.write(f'📝 Adding {product_name} to {target_file}...')
        
        # Read current file
        with open(target_file, 'r') as f:
            content = f.read()
        
        # Check if product ID already exists (not in comments)
        lines = content.split('\n')
        for line in lines:
            if f"'{product_id}'" in line and not line.strip().startswith('#'):
                self.stdout.write(f'ℹ️  Product {product_name} is already in ACTIVE_PRODUCTS')
                return
        
        # Add product ID to the list
        pattern = r'(ACTIVE_PRODUCTS = \[)(.*?)(\])'
        
        def replacer(match):
            start = match.group(1)
            existing = match.group(2)
            end = match.group(3)
            
            # Add new product ID with comment
            new_entry = f"\n    '{product_id}',  # {product_name}"
            return f"{start}{existing}{new_entry}\n{end}"
        
        new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)
        
        # Write back to file
        with open(target_file, 'w') as f:
            f.write(new_content)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Added {product_name} to ACTIVE_PRODUCTS'))

    def _remove_product_from_list(self, product_id, product_name, target_file):
        """Remove product ID from ACTIVE_PRODUCTS list"""
        self.stdout.write(f'📝 Removing {product_name} from {target_file}...')
        
        # Read current file
        with open(target_file, 'r') as f:
            content = f.read()
        
        # Check if product ID exists
        if f"'{product_id}'" not in content:
            self.stdout.write(f'ℹ️  Product {product_name} is not in ACTIVE_PRODUCTS')
            return
        
        # Remove product ID and its comment line
        pattern = rf"\s*'{product_id}',\s*# {re.escape(product_name)}\s*\n?"
        new_content = re.sub(pattern, '', content)
        
        # Write back to file
        with open(target_file, 'w') as f:
            f.write(new_content)
        
        self.stdout.write(self.style.WARNING(f'❌ Removed {product_name} from ACTIVE_PRODUCTS'))

    def _list_available_products(self):
        """List all products in ACTIVE_PRODUCTS"""
        from apps.subscriptions.metadata import ACTIVE_PRODUCTS
        
        self.stdout.write('\n📦 Products in ACTIVE_PRODUCTS\n')
        self.stdout.write('='*60)
        
        if ACTIVE_PRODUCTS:
            for idx, product_id in enumerate(ACTIVE_PRODUCTS, 1):
                try:
                    product = Product.objects.get(id=product_id)
                    self.stdout.write(f'{idx:2d}. {product.name}')
                    self.stdout.write(f'    ID: {product.id}')
                    if product.description:
                        self.stdout.write(f'    Description: {product.description[:80]}...')
                    self.stdout.write()
                except (Product.DoesNotExist, Exception):
                    self.stdout.write(self.style.ERROR(f'{idx:2d}. ❌ Product {product_id} not found in database'))
        else:
            self.stdout.write(self.style.WARNING('No products in ACTIVE_PRODUCTS'))
        
        # Show all available products
        try:
            all_products = Product.objects.all().order_by('name')
            self.stdout.write(f'\n📋 All Products in Database ({all_products.count()} total)\n')
            self.stdout.write('='*60)
            
            for idx, product in enumerate(all_products, 1):
                status = '✅' if product.id in ACTIVE_PRODUCTS else '⭕'
                self.stdout.write(f'{idx:2d}. {status} {product.name} ({product.id})')
            
            self.stdout.write(f'\n✅ = In ACTIVE_PRODUCTS, ⭕ = Available to add')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not access database: {str(e)}'))
            self.stdout.write('Run this command in production environment to see all products.')
