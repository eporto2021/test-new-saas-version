"""
Management command to add features to Stripe products.

This updates the Stripe product metadata with features that will be displayed
in the subscription pages.

Usage:
    python manage.py add_product_features prod_T9Fmx6Ey5TNwLT "Feature 1,Feature 2,Feature 3"
    python manage.py add_product_features prod_T9Fmx6Ey5TNwLT --interactive
"""

import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from djstripe.models import Product


class Command(BaseCommand):
    help = 'Add features to Stripe product metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='Stripe product ID (e.g., prod_T9Fmx6Ey5TNwLT)'
        )
        parser.add_argument(
            'features',
            type=str,
            nargs='?',
            help='Comma-separated list of features'
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Interactive mode to enter features'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        features_input = options.get('features')
        interactive = options.get('interactive', False)
        
        # Set Stripe API key
        if settings.STRIPE_LIVE_MODE:
            stripe.api_key = settings.STRIPE_LIVE_SECRET_KEY
            env_name = "LIVE (Production)"
        else:
            stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
            env_name = "TEST (Development)"
        
        try:
            # Get product from database
            product = Product.objects.get(id=product_id)
            self.stdout.write(f'\n📦 Product: {product.name}')
            self.stdout.write(f'Environment: {env_name}')
            
            # Get features
            if interactive:
                features_input = self._get_features_interactive()
            elif not features_input:
                self.stdout.write(self.style.ERROR('Features required (or use --interactive)'))
                return
            
            # Parse features
            features = [f.strip() for f in features_input.split(',') if f.strip()]
            
            if not features:
                self.stdout.write(self.style.ERROR('No valid features provided'))
                return
            
            self.stdout.write(f'\n📝 Adding {len(features)} features:')
            for i, feature in enumerate(features, 1):
                self.stdout.write(f'  {i}. {feature}')
            
            # Update Stripe product metadata
            stripe_product = stripe.Product.modify(
                product_id,
                metadata={
                    'features': ','.join(features)
                }
            )
            
            # Update local database
            product.metadata = stripe_product.metadata
            product.save()
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated {product.name}'))
            self.stdout.write('Features are now available in subscription pages!')
            
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Product {product_id} not found in database'))
            self.stdout.write('Run: python manage.py sync_all_stripe_products')
            
        except stripe.error.StripeError as e:
            self.stdout.write(self.style.ERROR(f'Stripe error: {str(e)}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

    def _get_features_interactive(self):
        """Interactive mode to enter features"""
        self.stdout.write('\n📝 Enter features (one per line, empty line to finish):')
        features = []
        
        while True:
            try:
                feature = input('Feature: ').strip()
                if not feature:
                    break
                features.append(feature)
            except KeyboardInterrupt:
                self.stdout.write('\nCancelled.')
                return None
        
        if not features:
            self.stdout.write('No features entered.')
            return None
            
        return ','.join(features)
