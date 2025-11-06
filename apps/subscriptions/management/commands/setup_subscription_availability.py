from django.core.management.base import BaseCommand, CommandError
from djstripe.models import Product
from apps.subscriptions.models import SubscriptionAvailability


class Command(BaseCommand):
    help = 'Set up subscription availability records for all Stripe products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Specific product ID to set up (optional)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to set up availability for (optional)'
        )
        parser.add_argument(
            '--make-available',
            action='store_true',
            help='Set make_subscription_available to True for new records'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all current subscription availability settings'
        )

    def handle(self, *args, **options):
        if options.get('list'):
            self.list_availability()
            return

        product_id = options.get('product_id')
        user_id = options.get('user_id')
        make_available = options.get('make_available', False)

        if product_id:
            # Set up specific product
            try:
                product = Product.objects.get(id=product_id)
                user = None
                if user_id:
                    from apps.users.models import CustomUser
                    user = CustomUser.objects.get(id=user_id)
                self.setup_product(product, make_available, user)
            except Product.DoesNotExist:
                raise CommandError(f'Product with ID {product_id} not found')
            except CustomUser.DoesNotExist:
                raise CommandError(f'User with ID {user_id} not found')
        else:
            # Set up all products (global availability only)
            products = Product.objects.all()
            if not products.exists():
                self.stdout.write(self.style.WARNING('No products found in database'))
                return

            self.stdout.write(f'Setting up global availability for {products.count()} products...')
            for product in products:
                self.setup_product(product, make_available, None)

        self.stdout.write(self.style.SUCCESS('Setup complete!'))

    def setup_product(self, product, make_available, user=None):
        """Set up availability record for a single product"""
        availability, created = SubscriptionAvailability.objects.get_or_create(
            stripe_product=product,
            user=user,
            defaults={'make_subscription_available': make_available}
        )

        if created:
            status = "Available" if make_available else "Request Only"
            user_info = f" (User: {user.email})" if user else " (Global)"
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created: {product.name} - {status}{user_info}')
            )
        else:
            user_info = f" (User: {user.email})" if user else " (Global)"
            self.stdout.write(
                self.style.WARNING(f'⏭️  Already exists: {product.name} - {"Available" if availability.make_subscription_available else "Request Only"}{user_info}')
            )

    def list_availability(self):
        """List all current availability settings"""
        availabilities = SubscriptionAvailability.objects.select_related('stripe_product').all()
        
        if not availabilities.exists():
            self.stdout.write(self.style.WARNING('No subscription availability records found'))
            return

        self.stdout.write(self.style.SUCCESS('Current Subscription Availability Settings:'))
        self.stdout.write('=' * 60)
        
        for avail in availabilities:
            status = "✅ Available" if avail.make_subscription_available else "⏳ Request Only"
            user_info = f" (User: {avail.user.email})" if avail.user else " (Global)"
            self.stdout.write(f'{avail.stripe_product.name}{user_info}')
            self.stdout.write(f'  ID: {avail.stripe_product.id}')
            self.stdout.write(f'  Status: {status}')
            self.stdout.write(f'  Updated: {avail.updated_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write('')
