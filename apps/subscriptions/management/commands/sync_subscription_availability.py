from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from djstripe.models import Product
from apps.subscriptions.models import SubscriptionAvailability

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync subscription availability records with Stripe products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id', 
            type=str, 
            help='Specific product ID to sync (optional)'
        )
        parser.add_argument(
            '--create-for-users', 
            action='store_true', 
            help='Create user-specific availability records for all users'
        )
        parser.add_argument(
            '--make-available', 
            action='store_true', 
            help='Set new records to available by default'
        )
        parser.add_argument(
            '--dry-run', 
            action='store_true', 
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--list', 
            action='store_true', 
            help='List all current availability records'
        )

    def handle(self, *args, **options):
        if options.get('list'):
            self.list_availability()
            return

        product_id = options.get('product_id')
        create_for_users = options.get('create_for_users', False)
        make_available = options.get('make_available', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                self.sync_product(product, create_for_users, make_available, dry_run)
            except Product.DoesNotExist:
                raise CommandError(f'Product with ID {product_id} not found')
        else:
            # Sync all products
            products = Product.objects.filter(active=True)
            if not products.exists():
                self.stdout.write(self.style.WARNING('No active products found in database'))
                return

            self.stdout.write(f'Syncing availability for {products.count()} active products...')
            for product in products:
                self.sync_product(product, create_for_users, make_available, dry_run)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Sync complete!'))
        else:
            self.stdout.write(self.style.WARNING('Dry run complete!'))

    def sync_product(self, product, create_for_users, make_available, dry_run=False):
        """Sync availability records for a specific product"""
        
        # Create global availability record if it doesn't exist
        global_created = self.create_global_availability(product, make_available, dry_run)
        
        if create_for_users:
            # Create user-specific records for all users
            user_created = self.create_user_specific_records(product, make_available, dry_run)
        else:
            user_created = 0

        # Report results
        if global_created or user_created:
            action = "Would create" if dry_run else "Created"
            self.stdout.write(f'{action} availability records for: {product.name}')
            if global_created:
                self.stdout.write(f'  - Global record')
            if user_created:
                self.stdout.write(f'  - {user_created} user-specific records')

    def create_global_availability(self, product, make_available, dry_run=False):
        """Create or update global availability record"""
        if dry_run:
            exists = SubscriptionAvailability.objects.filter(
                stripe_product=product,
                user__isnull=True
            ).exists()
            if exists:
                return False
            else:
                return True

        availability, created = SubscriptionAvailability.objects.get_or_create(
            stripe_product=product,
            user=None,  # Global
            defaults={'make_subscription_available': make_available}
        )
        return created

    def create_user_specific_records(self, product, make_available, dry_run=False):
        """Create user-specific availability records for all users"""
        users = User.objects.all()
        created_count = 0

        for user in users:
            if dry_run:
                exists = SubscriptionAvailability.objects.filter(
                    stripe_product=product,
                    user=user
                ).exists()
                if not exists:
                    created_count += 1
            else:
                availability, created = SubscriptionAvailability.objects.get_or_create(
                    stripe_product=product,
                    user=user,
                    defaults={'make_subscription_available': make_available}
                )
                if created:
                    created_count += 1

        return created_count

    def list_availability(self):
        """List all current availability records"""
        availabilities = SubscriptionAvailability.objects.select_related(
            'stripe_product', 'user'
        ).order_by('stripe_product__name', 'user__email')

        if not availabilities.exists():
            self.stdout.write(self.style.WARNING('No subscription availability records found'))
            return

        self.stdout.write(self.style.SUCCESS('Current Subscription Availability Settings:'))
        self.stdout.write('=' * 80)
        
        current_product = None
        for avail in availabilities:
            if avail.stripe_product != current_product:
                current_product = avail.stripe_product
                self.stdout.write('')
                self.stdout.write(self.style.HTTP_INFO(f'📦 {current_product.name}'))
                self.stdout.write(f'   Stripe ID: {current_product.id}')
                self.stdout.write('')

            status = "✅ Available" if avail.make_subscription_available else "⏳ Request Only"
            if avail.user:
                user_info = f"{avail.user.get_full_name() or avail.user.username} ({avail.user.email})"
                self.stdout.write(f'   👤 {user_info}: {status}')
            else:
                self.stdout.write(f'   🌍 Global: {status}')

        self.stdout.write('')
        self.stdout.write(f'Total records: {availabilities.count()}')
