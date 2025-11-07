"""
Management command to validate that all ACTIVE_PRODUCTS exist in the database.

This is typically run as part of the deployment release command to ensure
all configured products have been synced from Stripe.

Usage:
    python manage.py validate_subscriptions
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from djstripe.models import Product


class Command(BaseCommand):
    help = 'Validate that all ACTIVE_PRODUCTS exist in the database'

    def handle(self, *args, **options):
        # Get ACTIVE_PRODUCTS from settings (production/development) or metadata.py (fallback)
        if hasattr(settings, 'ACTIVE_PRODUCTS'):
            active_products = settings.ACTIVE_PRODUCTS
            # Determine the source based on whether we're in production mode
            if settings.STRIPE_LIVE_MODE:
                source = 'settings_production.py'
            else:
                source = 'settings.py'
        else:
            from apps.subscriptions.metadata import ACTIVE_PRODUCTS
            active_products = ACTIVE_PRODUCTS
            source = 'metadata.py'
        
        self.stdout.write(f'\n🔍 Validating ACTIVE_PRODUCTS from {source}')
        self.stdout.write('=' * 60)
        
        if not active_products:
            self.stdout.write(self.style.WARNING('⚠️  No products configured in ACTIVE_PRODUCTS'))
            return
        
        missing_products = []
        valid_products = []
        
        for product_id in active_products:
            try:
                product = Product.objects.get(id=product_id)
                valid_products.append(product)
                self.stdout.write(f'✅ {product.name} ({product_id})')
                
                # Check if product has active prices
                active_prices = product.prices.filter(active=True)
                if active_prices.exists():
                    self.stdout.write(f'   └─ {active_prices.count()} active price(s) found')
                else:
                    self.stdout.write(self.style.WARNING(f'   └─ ⚠️  No active prices found'))
                    
            except Product.DoesNotExist:
                missing_products.append(product_id)
                self.stdout.write(self.style.ERROR(f'❌ Product {product_id} not found in database'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'Valid products: {len(valid_products)}/{len(active_products)}')
        
        if missing_products:
            self.stdout.write(self.style.ERROR(f'\n❌ Missing products: {len(missing_products)}'))
            self.stdout.write(self.style.ERROR(f'   {", ".join(missing_products)}'))
            self.stdout.write('\n💡 Run: python manage.py djstripe_sync_models product price')
            raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All ACTIVE_PRODUCTS are valid!\n'))

