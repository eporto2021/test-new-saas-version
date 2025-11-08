# Subscription Product Features Guide

This guide explains how to display marketing features as bullet points on your subscription product cards in the "Subscriptions Available" tab.

## Overview

Your subscription system automatically displays marketing features for each product as a bulleted list with checkmarks. Features are retrieved from Stripe and displayed on product cards without any code changes needed.

## Where Features Are Displayed

Features appear on the **Subscriptions Available** page (`/ecommerce/`) in your application menu as "Subscriptions Availble".

Each subscription card shows:
- Product name and description
- Pricing information
- **✓ Feature list with green checkmarks**
- Subscribe/Request buttons

## How It Works

### 1. Configuration in Settings

Only products listed in `ACTIVE_PRODUCTS` will be displayed:

```python
# test/settings.py (development)
ACTIVE_PRODUCTS = [
    'prod_T9FO1AD2u8s2xX',  # Product 1
    'prod_T9G51eeTkn3ttj',  # Product 2
    'prod_T9FPSDcT4R6Ehr',  # Product 3
]

# test/settings_production.py (production)
ACTIVE_PRODUCTS = [
    'prod_LIVE_12345',  # Production products
]
```

### 2. Feature Retrieval Priority

The system checks for features in this order:

```
1. Stripe's native marketing_features field (PRIORITY)
   ↓ (if not found)
2. Product metadata['features']
   ↓ (if not found)
3. Product metadata['marketing_features']
   ↓ (if not found)
4. Empty list (no features displayed)
```

### 3. Automatic Display

The template at `templates/ecommerce/components/products_empty.html` automatically renders features with:
- Green checkmark icons
- Clean bullet-point formatting
- Responsive card layout

## Adding Features to Products

You have **two methods** to add features to your subscription products:

### Method 1: Stripe Dashboard (Recommended for non-technical users)

1. Log into your [Stripe Dashboard](https://dashboard.stripe.com)
2. Go to **Products** → Select your product
3. Scroll to **Marketing features** section
4. Click **Add feature** and enter feature text
5. Save changes
6. Run sync command:
   ```bash
   make sync
   ```

**Advantages:**
- Visual interface
- No command line needed
- Features visible in Stripe UI
- Best for team collaboration

### Method 2: Management Command (Recommended for automation)

Use the Django management command to add features programmatically:

```bash
# Basic syntax
make manage ARGS='add_product_features <product_id> "Feature 1, Feature 2, Feature 3"'

# Example
make manage ARGS='add_product_features prod_T9FO1AD2u8s2xX "Automated validation checks, Email notifications, Real-time monitoring"'
```

**Advantages:**
- Scriptable and automatable
- Version control friendly
- Batch updates possible
- No Stripe Dashboard access needed

## Examples

### Example 1: Adding Features via Command

```bash
# Add features to "Check each drop off has a pick up"
make manage ARGS='add_product_features prod_T9FO1AD2u8s2xX "Automated validation checks, Email notifications for mismatches, Real-time monitoring, Detailed audit reports"'

# Add features to "Role Based Staff Training Website"
make manage ARGS='add_product_features prod_T9G51eeTkn3ttj "Customizable training modules, Role-based access control, Progress tracking dashboard, Certificate generation, Multi-user support"'
```

### Example 2: Viewing Current Features

```bash
make shell
```

Then in the Django shell:

```python
from djstripe.models import Product
from django.conf import settings
from apps.subscriptions.metadata import ProductMetadata

for product_id in settings.ACTIVE_PRODUCTS:
    product = Product.objects.get(id=product_id)
    metadata = ProductMetadata.from_stripe_product(product)
    print(f'\n{product.name}:')
    for feature in metadata.features:
        print(f'  ✓ {feature}')
```

### Example 3: How Features Appear

When displayed on the subscription card:

```
┌─────────────────────────────────────┐
│ Check each drop off has a pick up   │
│ Automated validation service        │
│                                     │
│ $49.99 / month                      │
│                                     │
│ ✓ Automated validation checks       │
│ ✓ Email notifications for mismatches│
│ ✓ Real-time monitoring              │
│ ✓ Detailed audit reports            │
│                                     │
│ [Subscribe - $49.99/month]          │
└─────────────────────────────────────┘
```

## Technical Details

### Code Location

- **Metadata retrieval**: `apps/subscriptions/metadata.py` (lines 36-69)
- **Template display**: `templates/ecommerce/components/products_empty.html` (lines 37-48)
- **View logic**: `apps/ecommerce/views.py` (line 36)
- **Management command**: `apps/subscriptions/management/commands/add_product_features.py`

### Feature Storage Format

Features are stored in Stripe as comma-separated values in the metadata:

```python
{
  "metadata": {
    "features": "Feature 1, Feature 2, Feature 3"
  }
}
```

Or as native Stripe marketing features:

```python
{
  "marketing_features": [
    {"name": "Feature 1"},
    {"name": "Feature 2"},
    {"name": "Feature 3"}
  ]
}
```

## Workflow

### Development Environment

1. Add products to `test/settings.py` → `ACTIVE_PRODUCTS`
2. Add features using Stripe Dashboard or management command
3. Run `make sync` to sync from Stripe
4. Features appear automatically on `/ecommerce/`

### Production Environment

1. Add products to `test/settings_production.py` → `ACTIVE_PRODUCTS`
2. Use **live mode** product IDs (`prod_live_***`)
3. Set `STRIPE_LIVE_MODE=True` in environment
4. Add features to production Stripe products
5. Deploy and run migrations (features sync automatically on deploy)

## Troubleshooting

### Features Not Showing Up

**Problem**: Features added but not displaying on subscription cards.

**Solutions**:
1. Verify product is in `ACTIVE_PRODUCTS` list
2. Run sync command: `make sync`
3. Check feature format in Stripe metadata
4. Verify Django has latest product data from Stripe

### Check Feature Configuration

```bash
make manage ARGS='shell -c "
from djstripe.models import Product
from apps.subscriptions.metadata import ProductMetadata

product = Product.objects.get(id=\"prod_YOUR_ID\")
metadata = ProductMetadata.from_stripe_product(product)
print(f\"Features: {metadata.features}\")
"'
```

### Product Not Found Error

**Error**: `No Product with ID "prod_XXX" found in database!`

**Solution**: Sync products from Stripe:
```bash
make sync
# or
make manage ARGS='djstripe_sync_models product price'
```

## Best Practices

1. **Use descriptive features**: "24/7 customer support" instead of "Support"
2. **Keep features concise**: 3-7 features per product is ideal
3. **Update regularly**: Keep features current with product capabilities
4. **Sync after changes**: Always run `make sync` after Stripe changes
5. **Test in development**: Verify features display correctly before production
6. **Use native Stripe fields**: Prefer Stripe Dashboard method for team collaboration

## Related Documentation

- [Subscription Sync Guide](SUBSCRIPTION_SYNC_GUIDE.md)
- [Subscription Request Feature](SUBSCRIPTION_REQUEST_FEATURE.md)
- [Management Commands Guide](MANAGEMENT_COMMANDS_GUIDE.md)

## Summary

- **Goal**: Display product features as bullet points in the Subscriptions Available tab
- **Configuration**: Just specify product IDs in `ACTIVE_PRODUCTS` settings
- **Feature Sources**: Stripe native field (preferred) or metadata field (fallback)
- **Display**: Automatic - no template changes needed
- **Updates**: Use Stripe Dashboard or management command, then sync

Your subscription system handles feature display automatically. Just add features to Stripe, and they'll appear as formatted bullet points on your product cards! ✨

