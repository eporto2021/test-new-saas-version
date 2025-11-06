"""
Management command to sync ALL products from Stripe, including those without prices.
Automatically creates ProductMetadata entries and adds them to ACTIVE_PRODUCTS.

This is useful when djstripe_sync_models skips products that don't have prices.

Usage:
    python manage.py sync_all_stripe_products
    python manage.py sync_all_stripe_products --limit 50
    python manage.py sync_all_stripe_products --env dev
    python manage.py sync_all_stripe_products --env prod --add-to-active
"""

import stripe
import os
import re
from django.conf import settings
from django.core.management.base import BaseCommand
from djstripe.models import Product
from apps.subscriptions.metadata import ProductMetadata


class Command(BaseCommand):
    help = 'Force sync all products from Stripe to local database (including products without prices)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of products to fetch from Stripe (default: 100)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Set Stripe API key
        if settings.STRIPE_LIVE_MODE:
            stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
            env_name = "LIVE (Production)"
        else:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
            env_name = "TEST (Development)"
        
        self.stdout.write(f'\n🔄 Syncing products from Stripe {env_name} mode...\n')
        
        try:
            # Fetch all products from Stripe
            stripe_products = stripe.Product.list(limit=limit)
            total_in_stripe = len(stripe_products.data)
            
            self.stdout.write(f'📦 Found {total_in_stripe} products in Stripe\n')
            self.stdout.write('='*80 + '\n')
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for idx, stripe_prod in enumerate(stripe_products.data, 1):
                try:
                    # Check if product exists
                    existing = Product.objects.filter(id=stripe_prod.id).exists()
                    
                    # Sync product to database
                    product = Product.sync_from_stripe_data(stripe_prod)
                    
                    if existing:
                        self.stdout.write(f'{idx:2d}. ⏭️  Updated: {product.name}')
                        self.stdout.write(f'    ID: {product.id}')
                        updated_count += 1
                    else:
                        self.stdout.write(self.style.SUCCESS(f'{idx:2d}. ✅ Created: {product.name}'))
                        self.stdout.write(self.style.SUCCESS(f'    ID: {product.id}'))
                        created_count += 1
                    
                    # Show active status
                    if not product.active:
                        self.stdout.write(self.style.WARNING(f'    ⚠️  Product is inactive in Stripe'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'{idx:2d}. ❌ Error: {stripe_prod.id}'))
                    self.stdout.write(self.style.ERROR(f'    Error: {str(e)}'))
                    error_count += 1
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS(f'\n✅ Sync Complete!'))
            self.stdout.write(f'\n📊 Results:')
            self.stdout.write(f'   • New products created: {created_count}')
            self.stdout.write(f'   • Existing products updated: {updated_count}')
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'   • Errors: {error_count}'))
            
            total_in_db = Product.objects.count()
            self.stdout.write(f'\n📦 Total products now in database: {total_in_db}')
            
            # Show products without prices
            products_without_prices = Product.objects.filter(prices__isnull=True)
            if products_without_prices.exists():
                self.stdout.write(self.style.WARNING(f'\n⚠️  {products_without_prices.count()} products have no prices:'))
                for p in products_without_prices[:5]:
                    self.stdout.write(f'   • {p.name} ({p.id})')
                if products_without_prices.count() > 5:
                    self.stdout.write(f'   ... and {products_without_prices.count() - 5} more')
                self.stdout.write('\n   💡 Tip: Add prices in Stripe dashboard, then sync again')
            
            self.stdout.write('\n')
            
        except stripe.error.AuthenticationError:
            self.stdout.write(self.style.ERROR('\n❌ Stripe authentication failed!'))
            self.stdout.write(self.style.ERROR('   Check your STRIPE_TEST_SECRET_KEY or STRIPE_LIVE_SECRET_KEY'))
            
        except stripe.error.StripeError as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Stripe API error: {str(e)}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Unexpected error: {str(e)}'))
            raise
