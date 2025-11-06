from django.core.management.base import BaseCommand
from djstripe.models import Product
from apps.services.models import Service


class Command(BaseCommand):
    help = "Set up default services linked to Stripe products"

    def handle(self, **options):
        self.stdout.write("Setting up default services...")
        
        # Get all active Stripe products
        stripe_products = Product.objects.filter(active=True)
        
        if not stripe_products.exists():
            self.stdout.write(
                self.style.WARNING("No active Stripe products found. Run bootstrap_ecommerce first.")
            )
            return
        
        services_created = 0
        
        for product in stripe_products:
            # Create a service for each product
            service_slug = f"{product.name.lower().replace(' ', '-')}"
            
            service, created = Service.objects.get_or_create(
                slug=service_slug,
                defaults={
                    'name': product.name,
                    'description': product.description or f"Access to {product.name}",
                    'stripe_product': product,
                    'icon': self.get_icon_for_service(product.name),
                    'is_active': True,
                    'order': services_created
                }
            )
            
            if created:
                services_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created service: {service.name}")
                )
            else:
                self.stdout.write(
                    f"Service already exists: {service.name}"
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Setup complete! Created {services_created} new services.")
        )
    
    def get_icon_for_service(self, product_name):
        """Get appropriate Font Awesome icon based on product name"""
        name_lower = product_name.lower()
        
        if 'analytics' in name_lower or 'dashboard' in name_lower:
            return 'fa-solid fa-chart-line'
        elif 'api' in name_lower:
            return 'fa-solid fa-code'
        elif 'software' in name_lower or 'app' in name_lower:
            return 'fa-solid fa-cube'
        elif 'premium' in name_lower or 'pro' in name_lower:
            return 'fa-solid fa-star'
        elif 'basic' in name_lower:
            return 'fa-solid fa-circle'
        else:
            return 'fa-solid fa-cube'
