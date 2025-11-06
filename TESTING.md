# Testing Guide

## Running Tests

### All Tests
```bash
make test
```

### Specific App Tests
```bash
# Subscription tests
make manage ARGS="test apps.subscriptions"

# Ecommerce tests
make manage ARGS="test apps.ecommerce"

# Specific test file
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering"

# Specific test class
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering.ProductListFilteringTests"

# Specific test method
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering.ProductListFilteringTests.test_empty_list_shows_no_products"
```

### Verbose Output
```bash
make manage ARGS="test apps.subscriptions -v 2"
```

## Test Organization

### Subscriptions App
- `test_subscription.py` - Core subscription functionality
- `test_subscription_gating.py` - Feature gating tests
- `test_subscription_availability.py` - Availability model tests
- `test_product_list_filtering.py` - **Product filtering behavior** ⭐
- `test_active_products_filtering.py` - Comprehensive filtering tests
- `test_management_commands.py` - Management command tests
- `test_webhooks.py` - Stripe webhook tests

### Ecommerce App
- `test_digital_downloads.py` - Digital download functionality
- `test_subscription_filtering.py` - Subscription filtering in templates
- `test_product_configuration_filtering.py` - **ProductConfiguration filtering** ⭐
- `test_active_ecommerce_filtering.py` - Comprehensive ecommerce filtering

## Key Test Suites

### Product Filtering Tests ⭐

**Why These Matter**: These tests verify the core requirement that empty product lists show NO products, not all products.

**Location**:
- `apps/subscriptions/tests/test_product_list_filtering.py`
- `apps/ecommerce/tests/test_product_configuration_filtering.py`

**Run Them**:
```bash
make manage ARGS="test apps.subscriptions.tests.test_product_list_filtering apps.ecommerce.tests.test_product_configuration_filtering"
```

**What They Test**:
- Empty `ACTIVE_PRODUCTS` = no subscriptions shown ✅
- Empty `ACTIVE_ECOMMERCE_PRODUCT_IDS` = no one-time purchases shown ✅
- Only explicitly listed products appear ✅
- Invalid product IDs raise errors ✅

See `apps/subscriptions/tests/README_PRODUCT_FILTERING.md` for details.

## Writing New Tests

### Test Structure
```python
from django.test import TestCase

class MyFeatureTests(TestCase):
    """Test my feature"""
    
    def setUp(self):
        """Set up test data"""
        # Create test objects
        pass
    
    def test_feature_behavior(self):
        """Test that feature works as expected"""
        # Arrange
        # Act
        result = do_something()
        
        # Assert
        self.assertEqual(result, expected)
```

### Using Settings Overrides
```python
from django.test import override_settings

class MyTests(TestCase):
    @override_settings(ACTIVE_PRODUCTS=['prod_test_123'])
    def test_with_custom_settings(self):
        """Test with custom ACTIVE_PRODUCTS"""
        # When changing settings for metadata.py, reload the module
        from importlib import reload
        from apps.subscriptions import metadata
        reload(metadata)
        
        # Now test with the new settings
        products = list(metadata.get_active_products_with_metadata())
        self.assertEqual(len(products), 1)
```

### Testing Management Commands
```python
from io import StringIO
from django.core.management import call_command

def test_my_command(self):
    out = StringIO()
    call_command('my_command', stdout=out)
    output = out.getvalue()
    self.assertIn('Expected output', output)
```

## Continuous Integration

Tests run automatically on:
- Every git push (if CI configured)
- Every pull request
- Before deployment (recommended)

## Test Database

Tests use a separate database (`test_test`) that is:
- Created automatically before tests run
- Destroyed automatically after tests complete
- Isolated from your development database

## Coverage

To see test coverage:
```bash
make manage ARGS="coverage run -m unittest discover"
make manage ARGS="coverage report"
make manage ARGS="coverage html"  # Creates htmlcov/ directory
```

## Common Test Patterns

### Testing Views
```python
def test_view(self):
    self.client.login(username='user', password='pass')
    response = self.client.get('/path/')
    self.assertEqual(response.status_code, 200)
    self.assertIn('expected_content', response.content.decode())
```

### Testing Models
```python
def test_model_creation(self):
    obj = MyModel.objects.create(field='value')
    self.assertEqual(obj.field, 'value')
    self.assertTrue(obj.pk)  # Has a primary key
```

### Testing APIs
```python
def test_api_endpoint(self):
    response = self.client.get('/api/endpoint/')
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data['key'], 'value')
```

## Debugging Tests

### Run Single Test with Print Statements
```bash
make manage ARGS="test apps.myapp.tests.MyTest.test_method -v 2"
```

### Use Django Shell for Test Setup
```bash
make shell
>>> from apps.myapp.models import MyModel
>>> # Try things out
```

### Check Test Database
```bash
# While tests are running (in another terminal)
make dbshell
```

## Best Practices

1. ✅ **One assertion per test** (ideally) - makes failures clearer
2. ✅ **Descriptive test names** - `test_empty_list_shows_nothing` not `test_1`
3. ✅ **Arrange-Act-Assert pattern** - Setup, execute, verify
4. ✅ **Independent tests** - Each test should run independently
5. ✅ **Test edge cases** - Empty lists, null values, invalid inputs
6. ✅ **Use fixtures sparingly** - Prefer explicit setup for clarity
7. ✅ **Clean up after tests** - Use tearDown() if needed
8. ✅ **Mock external services** - Don't call real Stripe API in tests

## Troubleshooting

### Tests Pass Locally But Fail in CI
- Check database differences (SQLite vs PostgreSQL)
- Check environment variables
- Check for timing issues

### Tests Are Slow
- Use `setUpClass()` for expensive one-time setup
- Mock external calls
- Use in-memory database for read-only tests

### Tests Are Flaky
- Check for timing issues (use Django's `TransactionTestCase` if needed)
- Check for shared state between tests
- Check for random data affecting results

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django Test Case Classes](https://docs.djangoproject.com/en/stable/topics/testing/tools/)
- [dj-stripe Testing](https://dj-stripe.readthedocs.io/en/stable/testing/)

