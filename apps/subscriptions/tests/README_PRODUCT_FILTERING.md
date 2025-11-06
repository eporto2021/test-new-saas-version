# Product Filtering Tests

## Overview

These tests verify the core product filtering behavior introduced to ensure explicit control over which products are displayed in the store.

## Key Behavior Being Tested

**Critical Requirement**: Empty product lists (`ACTIVE_PRODUCTS = []` or `ACTIVE_ECOMMERCE_PRODUCT_IDS = []`) must show **NO products**, not default to showing all products.

## Test Files

### `test_product_list_filtering.py`
Tests the subscription product filtering logic in `apps/subscriptions/metadata.py`.

**Key Tests**:
- ✅ `test_empty_list_shows_no_products`: Verifies empty `ACTIVE_PRODUCTS` shows nothing
- ✅ `test_only_listed_products_shown`: Only explicitly listed products appear
- ✅ `test_all_listed_products_shown`: All listed products appear in order
- ✅ `test_invalid_product_raises_error`: Invalid product IDs raise errors

### `test_active_products_filtering.py`
Comprehensive tests for subscription product filtering including:
- Product ordering
- Metadata extraction
- Price displays
- Multiple product scenarios
- `ACTIVE_PRODUCT_IDS` set generation

### `test_product_configuration_filtering.py`
Tests the ecommerce `ProductConfiguration` filtering logic.

**Key Tests**:
- ✅ `test_only_active_configs_queryable`: Only `is_active=True` configs show
- ✅ `test_empty_when_all_inactive`: No products when all configs inactive
- ✅ `test_deactivate_config`: Deactivating removes from results
- ✅ `test_reactivate_config`: Reactivating adds back to results

### `test_active_ecommerce_filtering.py`
Comprehensive tests for ecommerce product filtering including:
- `bootstrap_ecommerce` command behavior
- Deactivation logic
- Slug generation
- View filtering

## Running the Tests

```bash
# Run all product filtering tests
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering apps.ecommerce.tests.test_product_configuration_filtering"

# Run subscription filtering tests only
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering"

# Run ecommerce filtering tests only
make manage ARGS="test apps.ecommerce.tests.test_product_configuration_filtering"

# Run all tests with verbose output
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering -v 2"
```

## What's Being Tested

### 1. Subscription Products (`ACTIVE_PRODUCTS`)

**File**: `apps/subscriptions/metadata.py`  
**Function**: `get_active_products_with_metadata()`

**Behavior**:
- Empty list → No products displayed
- Product IDs listed → Only those products displayed
- Invalid ID → Raises `SubscriptionConfigError`

### 2. Ecommerce Products (`ACTIVE_ECOMMERCE_PRODUCT_IDS`)

**File**: `apps/ecommerce/management/commands/bootstrap_ecommerce.py`  
**Command**: `python manage.py bootstrap_ecommerce`

**Behavior**:
- Empty list → All `ProductConfiguration` objects deactivated
- Product IDs listed → Only those get `ProductConfiguration` objects with `is_active=True`
- Unlisted products → Existing `ProductConfiguration` objects deactivated

**File**: `apps/ecommerce/views.py`  
**View**: `ecommerce_home()`

**Query**: `ProductConfiguration.objects.filter(is_active=True)`

## Why These Tests Matter

Before these changes, the system had fallback behavior:
- Empty `ACTIVE_PRODUCTS` → showed ALL active products in database
- Empty `ACTIVE_ECOMMERCE_PRODUCT_IDS` → created configs for ALL one-time products

This made it impossible to have "no products" during development or in environments where you don't want products displayed.

## Test Coverage

✅ Empty lists show no products  
✅ Only explicitly listed products show  
✅ Unlisted products are hidden  
✅ Product ordering is preserved  
✅ Invalid IDs raise errors  
✅ ProductConfiguration activation/deactivation works correctly  

## Related Documentation

- `docs/AUTOMATIC_SUBSCRIPTION_SYNC.md` - Deployment and sync workflow
- `test/settings.py` - Development product configuration
- `test/settings_production.py` - Production product configuration

