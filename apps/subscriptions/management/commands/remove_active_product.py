"""
Management command to remove a product from ACTIVE_PRODUCTS in settings files.

Usage:
    python manage.py remove_active_product prod_ABC123 --env development
    python manage.py remove_active_product prod_ABC123 --env production
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Remove a Stripe product from ACTIVE_PRODUCTS in settings.py or settings_production.py'

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

    def handle(self, *args, **options):
        product_id = options['product_id']
        env = options['env']
        
        # Normalize environment name
        if env in ['dev', 'development']:
            env = 'development'
            settings_file = 'test/settings.py'
        else:
            env = 'production'
            settings_file = 'test/settings_production.py'
        
        file_path = Path(settings_file)
        
        if not file_path.exists():
            raise CommandError(f'Settings file not found: {settings_file}')
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if product exists
        if product_id not in content:
            raise CommandError(f'Product {product_id} not found in {settings_file}')
        
        self.stdout.write(f'\nRemoving product {product_id} from {settings_file}...')
        
        # Remove the product entry
        original_content = content
        content = self._remove_product(content, product_id)
        
        if content == original_content:
            raise CommandError(f'Failed to remove product {product_id}')
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully removed {product_id} from {settings_file}'))
        self.stdout.write(self.style.SUCCESS(f'   Environment: {env}'))

    def _remove_product(self, content, product_id):
        """Remove product entry from ACTIVE_PRODUCTS"""
        # Pattern to match entire ProductMetadata entry including trailing comma
        # This handles multi-line entries
        pattern = rf"    ProductMetadata\(\s*stripe_id='{product_id}'.*?\),\n"
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)
        
        return content
