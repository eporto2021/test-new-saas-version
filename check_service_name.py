#!/usr/bin/env python
"""
Quick script to check Service names and user folders in production.
Run this in production: python check_service_name.py
"""
import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test.settings_production')
django.setup()

from apps.services.models import Service
from djstripe.models import Product

print("\n=== SERVICES IN DATABASE ===\n")
services = Service.objects.all()
if services.exists():
    for s in services:
        print(f"Service ID: {s.id}")
        print(f"  Name: '{s.name}'")
        print(f"  Slug: {s.slug}")
        print(f"  Stripe Product: {s.stripe_product.id} - {s.stripe_product.name}")
        print(f"  Active: {s.is_active}")
        print()
else:
    print("⚠️  NO SERVICES FOUND IN DATABASE!")
    print("This is likely the problem - you need to create Service records.\n")

print("\n=== USER 19 FOLDERS ===\n")
user_dir = Path("/code/user_programs/production_programs/user_19")
if user_dir.exists():
    for folder in user_dir.iterdir():
        if folder.is_dir():
            print(f"Folder: '{folder.name}'")
            template = folder / "template.html"
            print(f"  Has template.html: {template.exists()}")
            
            # Try to find matching service
            matching_services = Service.objects.filter(name=folder.name)
            if matching_services.exists():
                print(f"  ✅ MATCHES Service: {matching_services.first().name}")
            else:
                print(f"  ❌ NO MATCHING SERVICE FOUND")
                # Try case-insensitive search
                similar = Service.objects.filter(name__iexact=folder.name)
                if similar.exists():
                    print(f"     (Found similar: '{similar.first().name}')")
            print()
else:
    print(f"User 19 directory not found at: {user_dir}")

print("\n=== STRIPE PRODUCTS (for reference) ===\n")
products = Product.objects.filter(id__in=[
    'prod_T3ys3097fCjBPl',  # Check Each Drop off Has A Pick Up (production)
    'prod_TH8G6pq4cSCVBc',  # Role Based Staff Training Website (production)
])
for p in products:
    print(f"Product ID: {p.id}")
    print(f"  Name: '{p.name}'")
    print(f"  Has Service: {Service.objects.filter(stripe_product=p).exists()}")
    print()

