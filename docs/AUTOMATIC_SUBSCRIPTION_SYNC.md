# Automatic Subscription Sync on Deployment

This document explains the automatic Stripe product synchronization system that runs during deployment.

## Overview

When you deploy to production, the system automatically:
1. Runs database migrations
2. Syncs all products and prices from Stripe to the database
3. Validates that all configured products exist

This ensures your subscription products are always up-to-date without manual intervention.

## How It Works

### 1. Release Command (fly.toml)

The deployment release command automatically runs four steps:

```toml
[deploy]
  release_command = 'python manage.py migrate --noinput && python manage.py djstripe_sync_models product price && python manage.py bootstrap_ecommerce && python manage.py validate_subscriptions'
```

- **Step 1**: Run database migrations
- **Step 2**: Sync products and prices from Stripe
- **Step 3**: Bootstrap ecommerce products (create ProductConfiguration for one-time purchases)
- **Step 4**: Validate all ACTIVE_PRODUCTS exist

### 2. Product Configuration

Products are configured in two places:

**Development** (`test/settings.py`):
```python
# Subscription products (recurring billing) - TEST product IDs
ACTIVE_PRODUCTS = [
    'prod_TEST_ID',  # Your test subscription
]

# Ecommerce products (one-time purchases) - TEST product IDs
ACTIVE_ECOMMERCE_PRODUCT_IDS = [
    'prod_TEST_ECOMMERCE_ID',  # Your test one-time product
]
```

**Production** (`test/settings_production.py`):
```python
# Subscription products (recurring billing) - LIVE product IDs
ACTIVE_PRODUCTS = [
    'prod_TH8G6pq4cSCVBc',  # Role Based Staff Training Website
]

# Ecommerce products (one-time purchases) - LIVE product IDs
ACTIVE_ECOMMERCE_PRODUCT_IDS = [
    'prod_LIVE_ECOMMERCE_ID',  # Your live one-time product
]
```

Production settings automatically override development settings.

**Important**: 
- Empty lists (`[]`) mean **NO products** will be displayed
- Only products explicitly listed will be shown
- No fallback to "all available products"

### 3. Validation Command

The `validate_subscriptions` command checks:
- All products in ACTIVE_PRODUCTS exist in the database
- Each product has active prices
- Provides helpful error messages if something is missing

## Adding a New Subscription Product

### Simple 3-Step Process:

1. **Create product in Stripe** (live mode)
   - Go to https://dashboard.stripe.com/products
   - Create your product with **recurring pricing** (weekly, monthly, yearly, etc.)

2. **Add product ID to settings**
   ```python
   # test/settings_production.py
   ACTIVE_PRODUCTS = [
       'prod_TH8G6pq4cSCVBc',
       'prod_YOUR_NEW_PRODUCT_ID',  # Add here
   ]
   ```

3. **Deploy**
   ```bash
   fly deploy
   ```

That's it! The release command will automatically:
- Sync the new product from Stripe
- Validate it exists with prices
- Make it available in your app

## Adding a One-Time Purchase Product

### Simple 3-Step Process:

1. **Create product in Stripe** (live mode)
   - Go to https://dashboard.stripe.com/products
   - Create your product with **one-time pricing** (not recurring)

2. **Add product ID to settings**
   ```python
   # test/settings_production.py
   ACTIVE_ECOMMERCE_PRODUCT_IDS = [
       'prod_TH94dlNLdVaKvO',
       'prod_YOUR_NEW_PRODUCT_ID',  # Add here
   ]
   ```

3. **Deploy**
   ```bash
   fly deploy
   ```

That's it! The `bootstrap_ecommerce` command automatically:
- Creates ProductConfiguration entries for products in ACTIVE_ECOMMERCE_PRODUCT_IDS
- Deactivates products NOT in the list
- Makes them available in "One-time Purchases" section

**Only products explicitly listed will be displayed!**

## Manual Sync (Development)

For local development, you can sync products using the Makefile:

```bash
# Full restart with migrations and Stripe sync (mirrors production)
make restart

# Just sync without restarting
make sync

# Quick restart without sync
make restart-quick
```

Or manually run individual commands:

```bash
# Sync all products and prices from Stripe
python manage.py djstripe_sync_models product price

# Bootstrap ecommerce products
python manage.py bootstrap_ecommerce

# Validate your configuration
python manage.py validate_subscriptions

# List available products
python manage.py update_available_subscriptions list
```

## Management Commands

### validate_subscriptions
Validates that all ACTIVE_PRODUCTS exist in the database.

```bash
python manage.py validate_subscriptions
```

Output example:
```
🔍 Validating ACTIVE_PRODUCTS from settings_production.py
============================================================
✅ Role Based Staff Training Website (prod_TH8G6pq4cSCVBc)
   └─ 2 active price(s) found

============================================================
Valid products: 1/1

✅ All ACTIVE_PRODUCTS are valid!
```

### update_available_subscriptions
Manage products in ACTIVE_PRODUCTS list.

```bash
# List all products
python manage.py update_available_subscriptions list

# Add a product to production
python manage.py update_available_subscriptions production prod_ABC123

# Remove a product
python manage.py update_available_subscriptions production prod_ABC123 --remove
```

## Benefits

✅ **Automatic**: Products sync on every deployment
✅ **Reliable**: Validation ensures configuration is correct
✅ **Simple**: Just add product IDs to settings file
✅ **Fast**: Products loaded from database, not Stripe API
✅ **Safe**: Deployment fails if configuration is invalid

## Troubleshooting

### Product not showing in app?

1. Check it's in ACTIVE_PRODUCTS:
   ```bash
   fly ssh console -C "python manage.py validate_subscriptions"
   ```

2. Manually sync if needed:
   ```bash
   fly ssh console -C "python manage.py djstripe_sync_models product price"
   ```

3. Check product exists in Stripe live mode:
   - Visit https://dashboard.stripe.com/products
   - Ensure you're in live mode (not test mode)

### Deployment failing?

If deployment fails with product validation errors:

1. Check the error message - it will tell you which product is missing
2. Verify the product ID is correct in settings_production.py
3. Ensure the product exists in Stripe **live mode**
4. If needed, remove the product ID from ACTIVE_PRODUCTS temporarily

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Fly Deploy                            │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Release Command (fly.toml)                  │
│                                                          │
│  1. python manage.py migrate --noinput                  │
│  2. python manage.py djstripe_sync_models product price │
│  3. python manage.py validate_subscriptions             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Stripe Live API                             │
│         (Syncs products & prices)                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           PostgreSQL Database                            │
│     (Products & Prices stored locally)                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│          Django App (metadata.py)                        │
│   Reads from database, displays to users                │
└─────────────────────────────────────────────────────────┘
```

## Related Files

- `fly.toml` - Release command configuration
- `test/settings_production.py` - ACTIVE_PRODUCTS list
- `apps/subscriptions/metadata.py` - Product loading logic
- `apps/subscriptions/management/commands/validate_subscriptions.py` - Validation command
- `apps/subscriptions/management/commands/update_available_subscriptions.py` - Management command

