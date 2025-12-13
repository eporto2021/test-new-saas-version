from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from djstripe.enums import PriceType
from djstripe.models import Product
from stripe.error import AuthenticationError

from apps.ecommerce.models import ProductConfiguration
from apps.utils.billing import create_stripe_api_keys_if_necessary


class Command(BaseCommand):
    help = "Bootstraps your Stripe ecommerce setup"

    def handle(self, **options):
        try:
            if create_stripe_api_keys_if_necessary():
                print("Added Stripe secret key to the database...")
            # due to an issue in djstripe sometimes failing on unsynced data,
            # we need to sync prices once before syncing both products and prices
            print("Syncing products and prices from Stripe")
            call_command("djstripe_sync_models", "price")
            call_command("djstripe_sync_models", "product", "price")
            
            # Get the list of active ecommerce product IDs from settings
            active_ecommerce_ids = getattr(settings, 'ACTIVE_ECOMMERCE_PRODUCT_IDS', [])
            
            if active_ecommerce_ids:
                # Only create product configurations for products in ACTIVE_ECOMMERCE_PRODUCT_IDS
                print(
                    f"Creating product configurations for {len(active_ecommerce_ids)} "
                    f"products from ACTIVE_ECOMMERCE_PRODUCT_IDS"
                )
                for product_id in active_ecommerce_ids:
                    try:
                        product = Product.objects.get(id=product_id)
                        print(f"Creating/activating product configuration for {product.name}")
                        config, created = ProductConfiguration.objects.get_or_create(
                            product=product,
                            defaults={
                                "slug": slugify(product.name),
                                "is_active": True,
                                "overview": product.description or f"{product.name}",
                            },
                        )
                        # Ensure it's active if it already existed
                        if not created and not config.is_active:
                            config.is_active = True
                            config.save()
                            print(f"Activated product configuration for {product.name}")
                    except Product.DoesNotExist:
                        print(
                            f"Warning: Product {product_id} not found in database. "
                            f"Make sure it's synced from Stripe."
                        )
            else:
                # If ACTIVE_ECOMMERCE_PRODUCT_IDS is empty, show nothing
                print("ACTIVE_ECOMMERCE_PRODUCT_IDS is empty - no one-time purchase products will be displayed")
            
            # Always deactivate ProductConfigurations that are not in ACTIVE_ECOMMERCE_PRODUCT_IDS
            # (including ALL products if the list is empty)
            configs_to_deactivate = ProductConfiguration.objects.filter(
                is_active=True
            ).exclude(product__id__in=active_ecommerce_ids)
            if configs_to_deactivate.exists():
                print(f"Deactivating {configs_to_deactivate.count()} product(s) not in ACTIVE_ECOMMERCE_PRODUCT_IDS")
                for config in configs_to_deactivate:
                    print(f"  Deactivating: {config.product.name}")
                    config.is_active = False
                    config.save()
        except AuthenticationError:
            print(
                "\n======== ERROR ==========\n"
                "Failed to authenticate with Stripe! Check your Stripe key settings.\n"
                "More info: https://docs.saaspegasus.com/subscriptions.html#getting-started"
            )
