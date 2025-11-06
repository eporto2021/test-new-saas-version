"""
Management command to list all active products.

Usage:
    python manage.py list_active_products
    python manage.py list_active_products --env development
    python manage.py list_active_products --env production
"""

from django.core.management.base import BaseCommand
from apps.subscriptions.metadata import ACTIVE_PRODUCTS


class Command(BaseCommand):
    help = 'List all active products from ACTIVE_PRODUCTS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--env',
            type=str,
            choices=['development', 'production', 'dev', 'prod'],
            required=False,
            help='Show which environment (optional - shows current by default)'
        )

    def handle(self, *args, **options):
        from django.conf import settings
        
        env = options.get('env')
        if env:
            env_name = 'development' if env in ['dev', 'development'] else 'production'
            self.stdout.write(f'\nShowing products for: {env_name}')
        else:
            # Detect current environment
            if hasattr(settings, 'STRIPE_LIVE_MODE') and settings.STRIPE_LIVE_MODE:
                env_name = 'production (LIVE)'
            else:
                env_name = 'development (TEST)'
            self.stdout.write(f'\nCurrent environment: {env_name}')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(f'Active Products ({len(ACTIVE_PRODUCTS)} total)\n')
        self.stdout.write('='*80 + '\n')
        
        if not ACTIVE_PRODUCTS:
            self.stdout.write(self.style.WARNING('No active products found!'))
            self.stdout.write('\nTo add products, use:')
            self.stdout.write('  python manage.py add_active_product <product_id> --env development')
            return
        
        for idx, product in enumerate(ACTIVE_PRODUCTS, 1):
            self.stdout.write(f'\n{idx}. {self.style.SUCCESS(product.name)}')
            self.stdout.write(f'   Stripe ID: {product.stripe_id}')
            self.stdout.write(f'   Slug: {product.slug}')
            self.stdout.write(f'   Description: {product.description}')
            self.stdout.write(f'   Default: {"Yes" if product.is_default else "No"}')
            self.stdout.write(f'   Features: {len(product.features)} listed')
            
            if product.features:
                for feature in product.features[:3]:  # Show first 3 features
                    self.stdout.write(f'     • {feature}')
                if len(product.features) > 3:
                    self.stdout.write(f'     ... and {len(product.features) - 3} more')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(f'\nTotal: {len(ACTIVE_PRODUCTS)} products')
        
        # Count defaults
        defaults = [p for p in ACTIVE_PRODUCTS if p.is_default]
        if len(defaults) == 0:
            self.stdout.write(self.style.WARNING('⚠️  Warning: No default product set!'))
        elif len(defaults) > 1:
            self.stdout.write(self.style.WARNING(f'⚠️  Warning: {len(defaults)} products set as default (should be 1)'))
        else:
            self.stdout.write(f'Default product: {defaults[0].name}')
        
        self.stdout.write('\n')
