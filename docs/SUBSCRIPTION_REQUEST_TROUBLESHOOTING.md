# Fixing the "Request Subscription" Button Error - Complete Guide

## The Problem
When users clicked the "Request Subscription" button, they got this error:
```
There was an error submitting your request. Please try again or contact support.
```

The logs showed:
```
ERROR "test.subscription" Error creating subscription request: No Product matches the given query.
```

## Root Cause Analysis
The issue was that the system was trying to find a Stripe Product with ID `prod_T9FO1AD2u8s2xX` in the local database, but this product didn't exist locally. This happened because:

1. **Product IDs were configured** in `apps/subscriptions/metadata.py` in the `ACTIVE_PRODUCTS` list
2. **Products weren't synced** from Stripe to the local database
3. **The subscription request view** tried to look up the product using `get_object_or_404(Product, id=product_id)` but it didn't exist

## The Solution: Sync Products from Stripe

### Step 1: Identify Available Sync Commands
The codebase has several commands to sync products from Stripe:

1. **`bootstrap_subscriptions`** - Sets up API keys and syncs products/prices
2. **`sync_all_stripe_products`** - Syncs all products (including those without prices)
3. **`djstripe_sync_models`** - Standard djstripe sync command

### Step 2: Run the Bootstrap Command
```bash
docker compose run --rm web python manage.py bootstrap_subscriptions
```

**What this command does:**
- ✅ Creates Stripe API keys in the database
- ✅ Syncs all products from Stripe to local database
- ✅ Syncs all prices from Stripe to local database
- ✅ Provides updated product configuration

### Step 3: Verify the Fix
After running the command, you should see output like:
```
Added Stripe secret key to the database...
Syncing products and prices from Stripe
...
Synced 20 Product for sk_test_...YKoJ
```

The specific product `prod_T9FO1AD2u8s2xX` ("Check each drop off has a pick up") should now be in your database.

## How the Subscription Request System Works

### User Flow:
1. User goes to `/ecommerce/` (Subscriptions Available tab)
2. User sees products with "Request Subscription" buttons
3. User clicks the button
4. System creates a `SubscriptionRequest` record
5. Admin receives email notification
6. User sees success message

### Technical Flow:
1. **Template** (`templates/ecommerce/components/products_empty.html`) shows the button
2. **Form** submits to `/subscriptions/request/<product_id>/`
3. **View** (`apps/subscriptions/views/views.py` line 359) handles the request
4. **Database lookup** finds the product using `get_object_or_404(Product, id=product_id)`
5. **Record creation** creates a `SubscriptionRequest` object
6. **Email notification** sent to admins

## Available Management Commands

### 1. `bootstrap_subscriptions` (Recommended for initial setup)
```bash
docker compose run --rm web python manage.py bootstrap_subscriptions
```
- Sets up API keys
- Syncs products and prices
- Provides configuration template

### 2. `sync_all_stripe_products` (For comprehensive sync)
```bash
docker compose run --rm web python manage.py sync_all_stripe_products
```
- Syncs ALL products (including those without prices)
- More detailed output
- Better error handling

### 3. `djstripe_sync_models` (Standard djstripe)
```bash
docker compose run --rm web python manage.py djstripe_sync_models product price
```
- Standard djstripe sync
- Only syncs products with prices

## Prevention Tips

### 1. Regular Syncing
Run sync commands after:
- Creating new products in Stripe
- Making changes to product configurations
- Setting up new environments

### 2. Environment Setup
Always run `bootstrap_subscriptions` when:
- Setting up a new development environment
- Deploying to a new server
- After pulling changes that include new product IDs

### 3. Configuration Management
- Keep `ACTIVE_PRODUCTS` in `metadata.py` in sync with your Stripe account
- Use the management commands to update configurations
- Test subscription requests after configuration changes

## Troubleshooting

### If you still get "No Product matches the given query":
1. Check if the product ID exists in Stripe
2. Run `bootstrap_subscriptions` again
3. Verify the product is in the `ACTIVE_PRODUCTS` list
4. Check the database: `Product.objects.filter(id='prod_XXXXX').exists()`

### If sync commands fail:
1. Check your Stripe API keys in settings
2. Verify you're using the correct environment (test vs live)
3. Check Stripe dashboard for product status
4. Look for authentication errors in the output

## Key Files Involved

- **`apps/subscriptions/metadata.py`** - Product configuration
- **`apps/subscriptions/views/views.py`** - Request subscription view
- **`apps/subscriptions/models.py`** - SubscriptionRequest model
- **`templates/ecommerce/components/products_empty.html`** - Request button template
- **`apps/subscriptions/urls.py`** - URL routing

## Quick Reference

### Most Common Fix:
```bash
docker compose run --rm web python manage.py bootstrap_subscriptions
```

### Check if product exists:
```python
from djstripe.models import Product
Product.objects.filter(id='prod_XXXXX').exists()
```

### View all products in database:
```python
from djstripe.models import Product
for p in Product.objects.all():
    print(f"{p.id}: {p.name}")
```

This guide should help you understand and fix similar issues in the future! 🚀
