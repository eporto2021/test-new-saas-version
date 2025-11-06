# Testing Guide

This guide explains how to run unit tests for this Django project.

## Prerequisites

- Docker and Docker Compose installed
- Project dependencies installed via `uv`

## Quick Start

### Run All Tests
```bash
make test
```

This is the recommended way to run all tests as it handles Docker containers and database setup automatically.

**Note:** The `make test` command may show "up to date" if the target is cached. To force execution, use the direct Docker command below.

## Alternative Commands

### Using Docker Compose Directly
```bash
# Run all tests (RECOMMENDED - this actually works!)
docker compose run --rm web python manage.py test

# Run tests with keepdb (faster for subsequent runs)
docker compose run --rm web python manage.py test --keepdb

# Run tests with verbose output
docker compose run --rm web python manage.py test --verbosity=2
```

**Verified:** The Docker Compose command works correctly and will run all 81 tests across the project.

### Run Tests for Specific Apps
```bash
# Test only web app
docker compose run --rm web python manage.py test apps.web

# Test only subscriptions app
docker compose run --rm web python manage.py test apps.subscriptions

# Test only ecommerce app
docker compose run --rm web python manage.py test apps.ecommerce

# Test only API app
docker compose run --rm web python manage.py test apps.api

# Test only services app
docker compose run --rm web python manage.py test apps.services
```

### Run Specific Test Files
```bash
# Test specific test file
docker compose run --rm web python manage.py test apps.web.tests.test_basic_views

# Test specific test class
docker compose run --rm web python manage.py test apps.web.tests.test_basic_views.BasicViewTests

# Test specific test method
docker compose run --rm web python manage.py test apps.web.tests.test_basic_views.BasicViewTests.test_home_page
```

## Test Structure

The project contains **18 test files** across 5 main apps:

### apps/web/tests/ (6 test files)

#### `test_basic_views.py` - Basic View Tests
• Tests that the main public pages load correctly (HTTP 200 status)
• Verifies the landing page is accessible
• Checks that signup and login pages work
• Ensures terms of service page loads
• Validates robots.txt file is accessible

#### `test_logged_in_views.py` - Logged-in User View Tests
• Tests that user profile page requires authentication
• Verifies password change functionality requires login
• Checks that 2FA setup page requires authentication
• Ensures all protected views redirect to login when not authenticated

#### `test_api_schema.py` - API Schema Tests
• Tests that the API schema endpoint returns successfully (HTTP 200)
• Verifies the OpenAPI schema is accessible at `/api/schema/`

#### `test_meta_tags.py` - Meta Tag Tests
• Tests image URL generation for meta tags with fallback to default images
• Verifies absolute URL generation for meta tags
• Checks static and media file URL resolution
• Tests WebSocket URL generation (HTTP vs HTTPS)
• Ensures proper URL handling for different storage backends

#### `test_markdown_tags.py` - Markdown Template Tag Tests
• Tests basic markdown rendering (headings, bold, italic)
• Verifies code block rendering with syntax highlighting
• Checks XSS protection by sanitizing script tags and onclick attributes
• Tests that allowed HTML tags are preserved
• Validates image tag rendering with proper attributes
• Ensures malicious protocols (javascript:) are sanitized
• Tests template filter integration
• Verifies nested HTML tag handling

#### `test_missing_migrations.py` - Migration Validation Tests
• Tests that there are no pending database migrations
• Ensures all model changes have been properly migrated
• Prevents deployment issues from missing migrations

### apps/subscriptions/tests/ (7 test files)

#### `test_subscription.py` - Core Subscription Tests
• Tests subscription-gated views with real database subscriptions
• Verifies users with active subscriptions can access protected content
• Checks that users without subscriptions are redirected
• Tests plan-specific access control (limit_to_plans decorator)
• Validates subscription status checking functionality

#### `test_subscription_availability.py` - Subscription Availability Tests
• Tests creating global subscription availability settings
• Verifies user-specific availability overrides
• Checks unique constraint enforcement (one setting per product per user)
• Tests string representation of availability records
• Validates that same product can have both global and user-specific settings

#### `test_subscription_gating.py` - Subscription Gating Tests
• Tests subscription gating using mocked user methods (faster approach)
• Verifies protected views work with mocked active subscriptions
• Checks that views redirect when no active subscription exists
• Tests decorator functionality without full database setup

#### `test_subscription_template_tags.py` - Subscription Template Tag Tests
• Tests `user_has_active_subscription_for_product` template tag
• Verifies subscription availability checking for purchases
• Tests user-specific vs global availability precedence
• Checks active subscription navigation data generation
• Validates template tag integration in Django templates
• Tests different subscription statuses (active, canceled, etc.)

#### `test_management_commands.py` - Management Command Tests
• Tests `setup_subscription_availability` management command
• Verifies listing current availability settings
• Checks global availability setup with default settings
• Tests user-specific availability configuration
• Validates error handling for invalid product/user IDs
• Ensures command is idempotent (can run multiple times safely)

#### `test_subscriber_model.py` - Subscriber Model Tests
• Tests that the correct subscriber model is configured for djstripe
• Verifies CustomUser is set as the subscriber model

#### `test_webhooks.py` - Webhook Tests
• Tests Stripe webhook event parsing
• Verifies price data extraction from webhook events
• Checks subscription ID extraction
• Tests cancel_at_period_end flag parsing

### apps/ecommerce/tests/ (2 test files)

#### `test_digital_downloads.py` - Digital Download Tests
• Tests that download views require user authentication
• Verifies that only users with valid purchases can download files
• Checks 404 handling when no digital file exists
• Tests successful file download with proper headers
• Validates download link visibility on product access pages
• Ensures proper file attachment headers and content types

#### `test_subscription_filtering.py` - Subscription Filtering Tests
• Tests template filtering when users have no subscriptions
• Verifies filtering when users have subscriptions for some products
• Checks filtering when users have subscriptions for all products
• Tests different subscription statuses (active, trialing, past_due, canceled)
• Validates that inactive subscriptions don't hide products
• Tests template integration with subscription filtering logic

### apps/api/tests/ (1 test file)

#### `test_schema.py` - API Schema Tests
• Tests that API schema endpoint returns valid YAML
• Verifies that certain endpoints are filtered out (e.g., `/cms/`)
• Ensures API documentation is properly generated

### apps/services/tests/ (1 test file)

#### `test_navigation_deduplication.py` - Navigation Deduplication Tests
• Tests navigation generation when user has service access only
• Verifies navigation when user has subscription access only
• Checks deduplication logic (service takes priority over subscription)
• Tests mixed scenarios with both services and subscriptions
• Validates empty navigation for users with no access
• Tests anonymous user handling
• Verifies template tag integration for navigation

### pegasus/apps/examples/tests/ (1 test file)

#### `test_logged_in_views.py` - Example Logged-in View Tests
• Tests that example pages require authentication
• Verifies examples home page access
• Checks tasks example page
• Tests feature flags example page
• Validates object lifecycle example page
• Tests charts example page

## Troubleshooting

### Database Issues
If you encounter database-related errors:

```bash
# Drop and recreate test database
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS test_test;"
docker compose run --rm web python manage.py test
```

### Migration Issues
If you encounter migration dependency errors:

```bash
# Check migration status
docker compose run --rm web python manage.py showmigrations

# Run migrations first
docker compose run --rm web python manage.py migrate

# If you get "Cannot serialize function: lambda" errors, check for lambda functions in model fields
# and replace them with proper callable functions
```

### Container Issues
If Docker containers aren't running:

```bash
# Start containers in background
make start-bg

# Or start interactively
make start
```

## Test Options

### Useful Test Flags
- `--keepdb` - Keep test database for faster subsequent runs
- `--verbosity=2` - More detailed output
- `--debug-mode` - Enable debug mode
- `--parallel` - Run tests in parallel (if supported)
- `--failfast` - Stop on first failure

### Example with Multiple Options
```bash
docker compose run --rm web python manage.py test --keepdb --verbosity=2 --failfast
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
docker compose run --rm web python manage.py test --verbosity=2
```

## Performance Tips

1. **Use `--keepdb`** for faster test runs during development
2. **Run specific app tests** when working on a particular feature
3. **Use `--failfast`** to stop on first failure during development
4. **Run tests in parallel** if your CI supports it

## Expected Output

When tests run successfully, you should see:
```
Found 81 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................................................
----------------------------------------------------------------------
Ran 81 tests in X.XXXs

OK
```

## Common Issues

1. **"database already exists"** - Use `--keepdb` or drop the test database
2. **"could not translate host name 'db'"** - Ensure Docker containers are running
3. **Migration dependency errors** - Check djstripe and other package versions
4. **Import errors** - Verify all dependencies are installed correctly

## Getting Help

If you encounter issues:
1. Check that Docker containers are running: `docker compose ps`
2. Verify database connectivity: `make dbshell`
3. Check Django configuration: `docker compose run --rm web python manage.py check`
4. Review the project's Makefile for additional commands
