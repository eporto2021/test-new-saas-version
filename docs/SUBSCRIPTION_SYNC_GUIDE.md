# Subscription Sync Guide

This guide explains how to sync subscriptions from Stripe and make them available for purchase in your Django SaaS application.

## Overview

Your application has two main ways to control subscription availability:

1. **ACTIVE_PRODUCTS** - Simple list of product IDs that show in the "Subscriptions Available" tab
2. **SubscriptionAvailability** - Database records that control which products show Subscribe vs Request buttons

## Quick Start

### 1. Sync Products from Stripe

First, sync all products from your Stripe account to your local database:

```bash
# In Docker (local development)
docker compose run --rm web python manage.py bootstrap_subscriptions

# Or sync all products (including those without prices)
docker compose run --rm web python manage.py sync_all_stripe_products
```

### 2. Add Products to ACTIVE_PRODUCTS

Add products to the simple list that shows in "Subscriptions Available":

```bash
# Add a product to development settings
docker compose run --rm web python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT

# Add a product to production settings  
docker compose run --rm web python manage.py update_available_subscriptions production prod_T9Fmx6Ey5TNwLT
```

### 3. Set Subscription Availability

Control whether products show "Subscribe" or "Request Subscription" buttons:

```bash
# Make a product available for direct purchase (shows Subscribe button)
docker compose run --rm web python manage.py sync_subscription_availability --product-id prod_T9Fmx6Ey5TNwLT --make-available

# Create availability records for all users
docker compose run --rm web python manage.py sync_subscription_availability --create-for-users --make-available
```

## Detailed Commands

### Bootstrap Subscriptions (Recommended First Step)

```bash
docker compose run --rm web python manage.py bootstrap_subscriptions
```

**What it does:**
- Sets up Stripe API keys if needed
- Syncs products and prices from Stripe
- Creates default product configuration
- Shows you the ACTIVE_PRODUCTS code to add

**When to use:**
- Initial setup
- After creating new products in Stripe
- When products are missing from your database

### Sync All Stripe Products

```bash
docker compose run --rm web python manage.py sync_all_stripe_products
```

**What it does:**
- Fetches ALL products from Stripe (including those without prices)
- Syncs them to your local database
- Shows detailed results (new vs updated)
- Warns about inactive products

**Advantages over bootstrap_subscriptions:**
- ✅ Syncs products without prices
- ✅ More detailed output
- ✅ Better error handling
- ✅ Shows inactive products

### Update Available Subscriptions

```bash
# Add a product
docker compose run --rm web python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT

# Remove a product
docker compose run --rm web python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT --remove

# List current products
docker compose run --rm web python manage.py update_available_subscriptions list
```

**What it does:**
- Adds/removes product IDs to/from `ACTIVE_PRODUCTS` in `metadata.py`
- Controls which products show in "Subscriptions Available" tab
- Automatically adds helpful comments

### Sync Subscription Availability

```bash
# Sync all products
docker compose run --rm web python manage.py sync_subscription_availability

# Sync specific product
docker compose run --rm web python manage.py sync_subscription_availability --product-id prod_T9Fmx6Ey5TNwLT

# Make products available for purchase
docker compose run --rm web python manage.py sync_subscription_availability --make-available

# Create records for all users
docker compose run --rm web python manage.py sync_subscription_availability --create-for-users

# Dry run (see what would happen)
docker compose run --rm web python manage.py sync_subscription_availability --dry-run

# List current availability
docker compose run --rm web python manage.py sync_subscription_availability --list
```

**What it does:**
- Creates `SubscriptionAvailability` records
- Controls Subscribe vs Request Subscription buttons
- Can be set globally or per-user
- Shows detailed status of each product

### List Active Products

```bash
docker compose run --rm web python manage.py list_active_products
```

**What it does:**
- Shows all products in `ACTIVE_PRODUCTS`
- Displays product details (name, ID, features)
- Shows which environment you're in
- Warns if no default product is set

## Production Deployment

### For Fly.io Production

```bash
# SSH into production
fly ssh console --app test-blue-smoke-97

# Activate virtual environment
source .venv/bin/activate

# Run commands
python manage.py bootstrap_subscriptions
python manage.py update_available_subscriptions production prod_YOUR_PRODUCT_ID
python manage.py sync_subscription_availability --make-available
```

### Environment-Specific Commands

```bash
# Development (modifies apps/subscriptions/metadata.py)
python manage.py update_available_subscriptions development prod_ABC123

# Production (modifies test/settings_production.py)
python manage.py update_available_subscriptions production prod_ABC123
```

## Understanding the Two Systems

### ACTIVE_PRODUCTS (Simple List)
- **Location**: `apps/subscriptions/metadata.py`
- **Purpose**: Controls which products appear in "Subscriptions Available" tab
- **Format**: Simple list of product IDs
- **Example**:
```python
ACTIVE_PRODUCTS = [
    'prod_T9FO1AD2u8s2xX',  # Check each drop off has a pick up
    'prod_T9FHtgOwbWmPjB',  # Email Marketing Service
    'prod_T9FSGASyxDhv2c',  # Bulk Text Service
    'prod_T9FLz7TUL2aeI1'   # Payroll Service
]
```

### SubscriptionAvailability (Database Records)
- **Location**: Database table `subscriptions_subscriptionavailability`
- **Purpose**: Controls Subscribe vs Request Subscription buttons
- **Fields**:
  - `stripe_product`: The Stripe product
  - `user`: Specific user (null = global)
  - `make_subscription_available`: True = Subscribe button, False = Request button

## Common Workflows

### Adding a New Product

1. **Create product in Stripe dashboard**
2. **Sync to database**:
   ```bash
   docker compose run --rm web python manage.py sync_all_stripe_products
   ```
3. **Add to ACTIVE_PRODUCTS**:
   ```bash
   docker compose run --rm web python manage.py update_available_subscriptions development prod_NEW_PRODUCT_ID
   ```
4. **Make available for purchase**:
   ```bash
   docker compose run --rm web python manage.py sync_subscription_availability --product-id prod_NEW_PRODUCT_ID --make-available
   ```

### Making All Products Available

```bash
# Sync all products
docker compose run --rm web python manage.py sync_all_stripe_products

# Add all products to ACTIVE_PRODUCTS
docker compose run --rm web python manage.py update_available_subscriptions development --add-all

# Make all products available for purchase
docker compose run --rm web python manage.py sync_subscription_availability --make-available --create-for-users
```

### Troubleshooting Missing Products

1. **Check if product exists in database**:
   ```bash
   docker compose run --rm web python manage.py list_active_products
   ```

2. **If missing, sync from Stripe**:
   ```bash
   docker compose run --rm web python manage.py sync_all_stripe_products
   ```

3. **Check ACTIVE_PRODUCTS**:
   ```bash
   docker compose run --rm web python manage.py update_available_subscriptions list
   ```

4. **Check availability settings**:
   ```bash
   docker compose run --rm web python manage.py sync_subscription_availability --list
   ```

## File Locations

- **Development settings**: `apps/subscriptions/metadata.py`
- **Production settings**: `test/settings_production.py`
- **Management commands**: `apps/subscriptions/management/commands/`
- **Models**: `apps/subscriptions/models.py`

## Tips

1. **Always run `bootstrap_subscriptions` first** when setting up
2. **Use `sync_all_stripe_products`** if products are missing
3. **Check both ACTIVE_PRODUCTS and SubscriptionAvailability** for complete control
4. **Use `--dry-run`** to see what commands will do before running them
5. **Test in development first** before updating production

## Example Output

### bootstrap_subscriptions
```
Syncing products and prices from Stripe
Added Stripe secret key to the database...
Synced 20 Product for sk_test_...YKoJ
Done! Creating default product configuration

ACTIVE_PRODUCTS = [
    'prod_T9FO1AD2u8s2xX',  # Check each drop off has a pick up
    'prod_T9FHtgOwbWmPjB',  # Email Marketing Service
]
```

### sync_all_stripe_products
```
🔄 Syncing products from Stripe TEST (Development) mode...
📦 Found 19 products in Stripe
================================================================================
 1. ✅ Created: 10 on brand high converting HTML emails
    ID: prod_T9FnjBKswTE4To
 2. ⏭️  Updated: Weekly Upselling Report
    ID: prod_T9Fmx6Ey5TNwLT
================================================================================

✅ Sync Complete!

📊 Results:
   • New products created: 13
   • Existing products updated: 6

📦 Total products now in database: 19
```

### update_available_subscriptions
```
📝 Adding Weekly Upselling Report to apps/subscriptions/metadata.py...
✅ Added Weekly Upselling Report to ACTIVE_PRODUCTS

📦 Products in ACTIVE_PRODUCTS
============================================================
 1. Starter Package
    ID: prod_T3u59Bp4A9Vafm

 2. Weekly Upselling Report
    ID: prod_T9Fmx6Ey5TNwLT
```

This guide should help you sync and manage your subscription products effectively!
