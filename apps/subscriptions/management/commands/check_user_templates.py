"""
Management command to check user template paths and diagnose issues.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from djstripe.models import Product
from pathlib import Path
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Check user template paths and diagnose configuration issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check templates for specific user ID'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        self.stdout.write(self.style.SUCCESS('\n=== User Template Checker ===\n'))
        
        # Show BASE_DIR
        self.stdout.write(f"BASE_DIR: {settings.BASE_DIR}")
        
        # Show user_programs directory (uses environment-specific path)
        user_programs_dir = settings.USER_PROGRAMS_DIR
        env_name = "PRODUCTION" if settings.STRIPE_LIVE_MODE else "DEVELOPMENT"
        self.stdout.write(f"\nEnvironment: {env_name}")
        self.stdout.write(f"USER_PROGRAMS_DIR: {user_programs_dir}")
        self.stdout.write(f"Exists: {user_programs_dir.exists()}\n")
        
        # List all user directories
        if user_programs_dir.exists():
            self.stdout.write(self.style.WARNING("Found user directories:"))
            for user_dir in sorted(user_programs_dir.glob("user_*")):
                user_num = user_dir.name.replace("user_", "")
                self.stdout.write(f"  - {user_dir.name}")
                
                # List products for this user
                for product_dir in sorted(user_dir.iterdir()):
                    if product_dir.is_dir():
                        template_file = product_dir / "template.html"
                        exists_icon = "✓" if template_file.exists() else "✗"
                        self.stdout.write(f"    {exists_icon} {product_dir.name}")
                        if template_file.exists():
                            self.stdout.write(f"        Template: {template_file}")
        
        # Show all products in database
        self.stdout.write(self.style.WARNING("\nProducts in database:"))
        products = Product.objects.all()
        for product in products:
            self.stdout.write(f"  - ID: {product.id}")
            self.stdout.write(f"    Name: '{product.name}'")
            self.stdout.write(f"    Description: {product.description or 'N/A'}")
        
        # Check specific user if provided
        if user_id:
            self.stdout.write(self.style.WARNING(f"\nChecking user {user_id}:"))
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"  User: {user.username} ({user.email})")
                
                # Check their subscriptions
                from djstripe.models import Subscription
                subscriptions = Subscription.objects.filter(
                    customer__subscriber=user,
                    status__in=['active', 'trialing']
                )
                
                self.stdout.write(f"\n  Active subscriptions: {subscriptions.count()}")
                
                for subscription in subscriptions:
                    if subscription.items.exists():
                        item = subscription.items.first()
                        product = item.price.product
                        
                        self.stdout.write(f"\n  Product: '{product.name}'")
                        
                        # Check if template exists
                        template_path = user_programs_dir / f"user_{user.id}" / product.name / "template.html"
                        self.stdout.write(f"  Looking for: {template_path}")
                        
                        if template_path.exists():
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Template EXISTS"))
                        else:
                            self.stdout.write(self.style.ERROR(f"  ✗ Template NOT FOUND"))
                            
                            # Show what directory name they should use
                            user_product_dir = user_programs_dir / f"user_{user.id}"
                            if user_product_dir.exists():
                                self.stdout.write(f"\n  Available directories for user_{user.id}:")
                                for dir in user_product_dir.iterdir():
                                    if dir.is_dir():
                                        self.stdout.write(f"    - {dir.name}")
                                
                                self.stdout.write(self.style.WARNING(
                                    f"\n  ACTION NEEDED: Either rename the directory to match product name,"
                                ))
                                self.stdout.write(self.style.WARNING(
                                    f"  or update product name in database to match directory name."
                                ))
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
        
        self.stdout.write(self.style.SUCCESS('\n=== Check Complete ===\n'))

