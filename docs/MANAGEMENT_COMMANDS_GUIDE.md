# Management Commands Guide

## Subscription Product Management Commands

Four management commands to help you manage products and the `ACTIVE_PRODUCTS` list in your settings files.

---

## 1. Sync All Stripe Products (NEW!)

### Command
```bash
python manage.py sync_all_stripe_products
```

### What it does
- Fetches **ALL** products from your Stripe account
- Syncs them to your local database
- Works even if products don't have prices
- Shows which products are new vs updated
- Warns about inactive products
- Lists products without prices

### Usage

**In Docker:**
```bash
docker exec test-new-saas-version-web-1 python manage.py sync_all_stripe_products
```

**With limit:**
```bash
docker exec test-new-saas-version-web-1 python manage.py sync_all_stripe_products --limit 50
```

### Example Output
```
🔄 Syncing products from Stripe TEST (Development) mode...
📦 Found 19 products in Stripe
================================================================================
 1. ✅ Created: 10 on brand high converting HTML emails
    ID: prod_T9FnjBKswTE4To
 2. ⏭️  Updated: Weekly Upselling Report
    ID: prod_T9Fmx6Ey5TNwLT
...
================================================================================

✅ Sync Complete!

📊 Results:
   • New products created: 13
   • Existing products updated: 6

📦 Total products now in database: 19

⚠️  13 products have no prices:
   • Product A (prod_ABC)
   • Product B (prod_DEF)
   
   💡 Tip: Add prices in Stripe dashboard, then sync again
```

### When to Use
- After creating new products in Stripe
- When `djstripe_sync_models` skips products
- Initial setup of your project
- When you notice products missing from your database

### Advantages over `djstripe_sync_models`
- ✅ Syncs products **without** prices
- ✅ More detailed output
- ✅ Shows inactive products
- ✅ Better error handling
- ✅ Easier to read results

---

## 2. Update Available Subscriptions (NEW!)

### Command
```bash
python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT
```

### What it does
- Adds/removes product IDs to/from `ACTIVE_PRODUCTS` in `metadata.py`
- Controls which products show in "Subscriptions Available" tab
- Uses simple product ID list instead of complex metadata objects
- Automatically adds helpful comments

### Usage

**Add a product:**
```bash
docker exec test-new-saas-version-web-1 python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT
```

**Remove a product:**
```bash
docker exec test-new-saas-version-web-1 python manage.py update_available_subscriptions development prod_T9Fmx6Ey5TNwLT --remove
```

**List current products:**
```bash
docker exec test-new-saas-version-web-1 python manage.py update_available_subscriptions list
```

### Example Output
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

### How it works
- **Development**: Modifies `apps/subscriptions/metadata.py`
- **Production**: Modifies `test/settings_production.py`
- **Simple**: Just adds product IDs like `'prod_ABC123'`
- **Smart**: Detects if product already exists (ignores comments)

### Before/After Example

**Before:**
```python
ACTIVE_PRODUCTS = [
    'prod_T3u59Bp4A9Vafm',  # Starter Package
]
```

**After:**
```python
ACTIVE_PRODUCTS = [
    'prod_T3u59Bp4A9Vafm',  # Starter Package
    'prod_T9Fmx6Ey5TNwLT',  # Weekly Upselling Report
]
```

---

## 3. List Active Products

### Command
```bash
python manage.py list_active_products
```

### What it does
- Shows all products currently in `ACTIVE_PRODUCTS`
- Displays product details (name, ID, slug, features)
- Shows which environment you're in (dev/prod)
- Warns if no default product is set

### Usage

**In Docker:**
```bash
docker exec test-new-saas-version-web-1 python manage.py list_active_products
```

**With environment flag:**
```bash
docker exec test-new-saas-version-web-1 python manage.py list_active_products --env production
docker exec test-new-saas-version-web-1 python manage.py list_active_products --env development
```

### Example Output
```
Current environment: development (TEST)
================================================================================
Active Products (5 total)

================================================================================

1. Starter Package
   Stripe ID: prod_T3u59Bp4A9Vafm
   Slug: starter-package
   Description: The Starter Package plan
   Default: Yes
   Features: 3 listed
     • Checks every drop off has a pick up program
     • Unlimited Usage
     • Free security & minor updates

2. Level Up Package
   Stripe ID: prod_T3uAydUSsWLfxO
   ...

================================================================================
Total: 5 products
Default product: Starter Package
```

---

## 2. Add Active Product

### Command
```bash
python manage.py add_active_product <PRODUCT_ID> --env <development|production>
```

### What it does
- Fetches product details from Stripe database
- Generates `ProductMetadata` code
- Adds it to `ACTIVE_PRODUCTS` in the appropriate settings file
- Automatically formats with proper indentation

### Required Arguments
- `product_id` - Stripe product ID (e.g., `prod_ABC123`)

### Optional Arguments
- `--env` - Target environment: `development` or `production` (default: development)
- `--default` - Set this product as the default

### Usage Examples

**Add to development settings:**
```bash
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_T3u59Bp4A9Vafm --env development
```

**Add to production settings:**
```bash
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC123XYZ --env production
```

**Add as default product:**
```bash
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC123 --env production --default
```

**Short flags:**
```bash
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC123 --env prod --default
```

### What gets added to settings

The command generates and adds code like this:

```python
ACTIVE_PRODUCTS = [
    ProductMetadata(
        stripe_id='prod_T3u59Bp4A9Vafm',
        slug='starter-package',
        name='Starter Package',
        features=[
            'Checks every drop off has a pick up program',
            'Unlimited Usage',
            'Free security & minor updates'
        ],
        price_displays={},
        description='The Starter Package plan',
        is_default=False
    ),
]
```

### Before Running

Make sure the product exists in your database:
```bash
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models Product
```

---

## 3. Remove Active Product

### Command
```bash
python manage.py remove_active_product <PRODUCT_ID> --env <development|production>
```

### What it does
- Removes a product from `ACTIVE_PRODUCTS` in the specified settings file
- Asks for confirmation before removing
- Preserves file formatting

### Required Arguments
- `product_id` - Stripe product ID to remove

### Optional Arguments
- `--env` - Target environment: `development` or `production` (default: development)

### Usage Examples

**Remove from development:**
```bash
docker exec test-new-saas-version-web-1 python manage.py remove_active_product prod_T3u59Bp4A9Vafm --env dev
```

**Remove from production:**
```bash
docker exec test-new-saas-version-web-1 python manage.py remove_active_product prod_ABC123 --env prod
```

### Safety Features
- Asks for confirmation before removing
- Shows which file will be modified
- Validates product exists before attempting removal

---

## Complete Workflow Example

### Scenario: Adding a new product to production

```bash
# 1. Sync Stripe products
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models Product

# 2. List all products to find the ID
docker exec test-new-saas-version-web-1 python manage.py shell
>>> from djstripe.models import Product
>>> for p in Product.objects.all():
...     print(f"{p.id}: {p.name}")
>>> exit()

# 3. Add the product to production settings
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC123XYZ --env production --default

# 4. Verify it was added
docker exec test-new-saas-version-web-1 python manage.py list_active_products --env production

# 5. (Optional) Remove old product
docker exec test-new-saas-version-web-1 python manage.py remove_active_product prod_OLD123 --env production
```

---

## Target Files

### Development Environment
**File:** `test/settings.py`

Products added here will be used when:
- Running locally with Docker
- `STRIPE_LIVE_MODE = False`
- Using test Stripe keys

### Production Environment
**File:** `test/settings_production.py`

Products added here will be used when:
- Deployed to production
- `STRIPE_LIVE_MODE = True`
- Using live Stripe keys

---

## Advanced Usage

### Get Product ID from Stripe Dashboard

1. Go to https://dashboard.stripe.com/products
2. Click on a product
3. Copy the product ID (starts with `prod_`)

### Get Product ID from CLI

```bash
docker exec test-new-saas-version-web-1 python manage.py shell
```

```python
from djstripe.models import Product

# List all products
for p in Product.objects.all():
    print(f"{p.id}: {p.name} (Active: {p.active})")

# Find by name
products = Product.objects.filter(name__icontains="starter")
for p in products:
    print(f"{p.id}: {p.name}")
```

### Batch Add Multiple Products

Create a shell script:

```bash
#!/bin/bash
# add_products.sh

PRODUCTS=(
    "prod_ABC123"
    "prod_DEF456"
    "prod_GHI789"
)

for product_id in "${PRODUCTS[@]}"; do
    docker exec test-new-saas-version-web-1 \
        python manage.py add_active_product "$product_id" --env production
done
```

---

## Tips & Best Practices

### 1. Always Sync First
Before adding products, sync with Stripe:
```bash
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models Product
```

### 2. Use Version Control
Before running commands, commit your current settings:
```bash
git add test/settings*.py
git commit -m "Before adding new product"
```

### 3. Test in Development First
```bash
# Add to dev first
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC --env dev

# Test it works
# Visit http://localhost:8000/ecommerce/

# Then add to production
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC --env prod
```

### 4. Set One Default
Only one product should have `is_default=True`. Use the `--default` flag:
```bash
docker exec test-new-saas-version-web-1 python manage.py add_active_product prod_ABC --env prod --default
```

### 5. Verify After Changes
```bash
docker exec test-new-saas-version-web-1 python manage.py list_active_products
```

---

## Troubleshooting

### "Product not found in database"
**Solution:** Sync Stripe data first
```bash
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models Product
```

### "Product already exists"
The command will ask if you want to update it. Type `yes` to replace the existing entry.

### Changes not reflecting on website
1. Restart the Django server:
```bash
docker-compose restart web
```

2. Or if using hot reload, just refresh your browser

### File permissions error
Make sure the settings files are writable by the Docker container.

---

## Environment Detection

The commands automatically detect your environment based on:

1. `STRIPE_LIVE_MODE` setting
2. Which Stripe keys are being used
3. The `--env` flag (overrides detection)

---

## Related Commands

### Stripe Sync Commands
```bash
# Sync all Stripe data
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models

# Sync specific models
docker exec test-new-saas-version-web-1 python manage.py djstripe_sync_models Product Price

# Bootstrap subscriptions
docker exec test-new-saas-version-web-1 python manage.py bootstrap_subscriptions
```

### Check Current Configuration
```bash
# Django shell
docker exec test-new-saas-version-web-1 python manage.py shell

# Then in Python:
from django.conf import settings
print(settings.STRIPE_LIVE_MODE)  # True = production, False = development
print(len(settings.PROJECT_METADATA.get('ACTIVE_PRODUCTS', [])))
```

---

## Subscription Request Management

### How Subscription Availability Works

The system now uses the `SubscriptionRequest` model to control which subscriptions are available to users:

1. **Default State**: All subscriptions show "Request Subscription" button
2. **After Request**: User sees "Request Submitted" message  
3. **Staff Approval**: Staff can approve requests in Django Admin
4. **After Approval**: User sees "Subscribe" button and can purchase

### Staff Workflow

1. **View Requests**: Go to Django Admin → Subscriptions → Subscription Requests
2. **Review**: Check user details, product info, and any messages
3. **Approve**: Change status from "Pending" to "Approved" 
4. **Result**: User immediately sees "Subscribe" button for that product

### Admin Features

- **Bulk Actions**: Approve multiple requests at once
- **Status Indicators**: Color-coded status display
- **User Links**: Direct links to user profiles
- **Product Info**: Shows Stripe product details
- **Filtering**: Filter by status, date, user type

---

## User Management Commands

Commands for creating and managing users in your Django application.

---

## 1. Create User

### Command
```bash
python manage.py create_user
```

### File Location
`apps/users/management/commands/create_user.py`

### What it does
- Creates a new user with customizable options
- Supports auto-login functionality
- Can open browser automatically with login instructions
- Provides default values for convenience
- Handles session creation for immediate login
- Includes browser automation with JavaScript bookmarklets

### Usage

**Basic user creation:**
```bash
# Docker
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username newuser \
  --email newuser@example.com \
  --password password123

# Local
python manage.py create_user \
  --username newuser \
  --email newuser@example.com \
  --password password123
```

**Create user with custom name:**
```bash
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username john \
  --email john@example.com \
  --password john123 \
  --first-name "John" \
  --last-name "Smith"
```

**Create superuser:**
```bash
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username admin \
  --email admin@example.com \
  --password admin123 \
  --superuser \
  --staff
```

**Create user with auto-login and browser:**
```bash
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username testuser \
  --email testuser@example.com \
  --password test123 \
  --auto-login \
  --open-browser
```

### Available Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--username` | ✅ | `user{N}` | Username for the new user |
| `--email` | ✅ | `{username}@example.com` | Email address for the new user |
| `--password` | ✅ | `defaultpassword123` | Password for the new user |
| `--first-name` | ❌ | "Default" | First name of the user |
| `--last-name` | ❌ | "User" | Last name of the user |
| `--superuser` | ❌ | False | Make user a superuser |
| `--staff` | ❌ | False | Give user staff access |
| `--auto-login` | ❌ | False | Automatically log in the user |
| `--open-browser` | ❌ | False | Open browser to localhost:8000 with login instructions |
| `--no-input` | ❌ | False | Skip confirmation prompts |

### File Structure & Implementation

The `create_user.py` command is a comprehensive Django management command with the following key features:

#### **Command Class Structure**
```python
class Command(BaseCommand):
    help = 'Creates a new user with default arguments'
    
    def add_arguments(self, parser):
        # Defines all command-line arguments
        
    def handle(self, *args, **options):
        # Main execution logic
```

#### **Key Implementation Features**

**1. Flexible Input Handling:**
- Accepts command-line arguments
- Prompts for missing values interactively
- Falls back to sensible defaults
- Supports `--no-input` for automation

**2. Auto-Login Functionality:**
- Creates Django sessions programmatically
- Uses `SessionStore` for session management
- Stores user authentication data
- Sets 30-day session expiration

**3. Browser Automation:**
- Opens Chrome browser to localhost:8000
- Provides JavaScript bookmarklet for auto-filling forms
- Includes manual login instructions as fallback
- Supports multiple browser opening methods

**4. Error Handling:**
- Validates username/email uniqueness
- Provides clear error messages
- Handles browser opening failures gracefully
- Includes confirmation prompts for safety

**5. Default Value Strategy:**
- Username: `user{N}` (incremental numbering)
- Email: `{username}@example.com`
- Password: `defaultpassword123`
- Names: "Default User"

#### **Dependencies**
```python
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import webbrowser
import subprocess
```

#### **Browser Integration Details**
- **Chrome Detection:** Tries multiple Chrome executable paths
- **JavaScript Bookmarklet:** Auto-fills login forms
- **Cross-Platform:** Works on macOS, Linux, Windows
- **Fallback:** Uses default browser if Chrome not found

#### **Session Management**
- Creates persistent database sessions
- Stores authentication backend information
- Handles session encoding properly
- Sets appropriate expiration times

### Example Output
```
Successfully created user "John Smith <john@example.com>"
  Username: john
  Email: john@example.com
  Full Name: John Smith
  Superuser: False
  Staff: False

User automatically logged in!
  Session Key: abc123def456
  Session expires in 30 days

Opening Chrome browser to http://localhost:8000...
Chrome browser opened to localhost:8000

=== LOGIN INSTRUCTIONS ===
Username/Email: john@example.com
Password: john123

=== METHOD 1: Auto-Fill Bookmarklet ===
1. Navigate to the login page in Chrome
2. Copy this entire line and paste it in the address bar:

javascript:(function(){var e=document.querySelector('input[name="email"],input[name="username"],input[name="login"],input[type="email"],input[id*="email"],input[id*="username"]');var p=document.querySelector('input[name="password"],input[type="password"],input[id*="password"]');if(e&&p){e.value='john@example.com';p.value='john123';e.dispatchEvent(new Event('input',{bubbles:true}));p.dispatchEvent(new Event('input',{bubbles:true}));alert('Form filled! Email: john@example.com');}else{alert('Form not found. Email: john@example.com\nPassword: john123');}})();

3. Press Enter
4. The form should auto-fill

=== METHOD 2: Manual Entry (if bookmarklet fails) ===
1. Go to the login page
2. Enter Email: john@example.com
3. Enter Password: john123
4. Click Login
```

### Advanced Usage & Troubleshooting

#### **Automation & Scripting**
```bash
# For CI/CD or automated testing
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --no-input \
  --username testuser \
  --email test@example.com \
  --password test123 \
  --superuser

# Bulk user creation script
for i in {1..5}; do
  docker exec test-new-saas-version-web-1 python manage.py create_user \
    --no-input \
    --username "user$i" \
    --email "user$i@example.com" \
    --password "password123"
done
```

#### **Development Workflow Integration**
```bash
# Quick test user with auto-login
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username devuser \
  --email dev@example.com \
  --password dev123 \
  --auto-login \
  --open-browser

# Admin user for testing
docker exec test-new-saas-version-web-1 python manage.py create_user \
  --username admin \
  --email admin@example.com \
  --password admin123 \
  --superuser \
  --staff \
  --auto-login
```

#### **Common Issues & Solutions**

**1. User Already Exists Error:**
```
CommandError: User with username "john" already exists
```
**Solution:** Use a different username or delete the existing user first.

**2. Browser Opening Fails:**
```
Failed to open Chrome: [Errno 2] No such file or directory: 'google-chrome'
```
**Solution:** The command will fall back to the default browser. Chrome detection works on most systems but may need adjustment for custom installations.

**3. Session Creation Issues:**
```
User created but auto-login failed: SessionBase.encode() missing 1 required positional argument
```
**Solution:** This was fixed in the current version. Ensure you're using the latest code.

**4. Permission Issues:**
```
PermissionError: [Errno 13] Permission denied: '/tmp/session_file'
```
**Solution:** Run with appropriate permissions or use `--no-input` to avoid temporary file creation.

#### **Customization Options**

**Modifying Default Values:**
Edit the file `apps/users/management/commands/create_user.py` and change the default values:
```python
# Line 100-103: Change default names
if not first_name:
    first_name = 'Your Default'  # Custom default
if not last_name:
    last_name = 'Name'           # Custom default
```

**Adding New Arguments:**
```python
def add_arguments(self, parser):
    # Add custom argument
    parser.add_argument(
        '--custom-field',
        type=str,
        help='Custom field for the user'
    )
```

**Browser Path Customization:**
```python
# Line 180+: Modify Chrome detection paths
chrome_commands = [
    ['open', '-a', 'Google Chrome', url],      # macOS
    ['google-chrome', '--new-tab', url],       # Linux
    ['chromium-browser', '--new-tab', url],    # Chromium
    ['chrome', '--new-tab', url],              # Windows
    ['start', 'chrome', url],                  # Windows alternative
    # Add your custom path here
]
```

#### **Security Considerations**

**Production Usage:**
- Always use strong passwords in production
- Consider using environment variables for sensitive data
- Disable browser opening in production environments
- Use `--no-input` for automated deployments

**Development Best Practices:**
- Use consistent naming conventions for test users
- Clean up test users regularly
- Document any custom modifications
- Test with different user types (regular, staff, superuser)

---

## 2. Promote User to Superuser

### Command
```bash
python manage.py promote_user_to_superuser
```

### What it does
- Promotes an existing user to superuser status
- Gives the user admin access to Django admin interface
- Sets both `is_superuser` and `is_staff` to `True`

### Usage

**Promote user by username:**
```bash
# Docker
docker exec test-new-saas-version-web-1 python manage.py promote_user_to_superuser john

# Local
python manage.py promote_user_to_superuser john
```

### Example Output
```
john successfully promoted to superuser and can now access the admin site
```

### Error Handling
- If username doesn't exist: `CommandError: No user with username/email john found!`

---

## 3. Delete User

### Command
```bash
python manage.py delete_user
```

### What it does
- Safely deletes a user from the database
- Requires confirmation before deletion
- Can find user by username or email

### Usage

**Delete user by username:**
```bash
# Docker
docker exec test-new-saas-version-web-1 python manage.py delete_user --username john

# Local
python manage.py delete_user --username john
```

**Delete user by email:**
```bash
docker exec test-new-saas-version-web-1 python manage.py delete_user --email john@example.com
```

### Example Output
```
Are you sure you want to delete the user 'john'? Type 'yes' to confirm: yes
User 'john' deleted successfully.
```

### Error Handling
- If no username/email provided: `CommandError: You must provide either --username or --email`
- If user not found: `CommandError: User not found`

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `sync_all_stripe_products` | Sync all products from Stripe | `python manage.py sync_all_stripe_products` |
| `update_available_subscriptions` | Add/remove products from ACTIVE_PRODUCTS | `python manage.py update_available_subscriptions development prod_ABC` |
| `list_active_products` | View all active products | `python manage.py list_active_products` |
| `add_active_product` | Add product to settings | `python manage.py add_active_product prod_ABC --env prod` |
| `remove_active_product` | Remove product from settings | `python manage.py remove_active_product prod_ABC --env dev` |
| `create_user` | Create new user with options | `python manage.py create_user --username john --email john@example.com --password john123` |
| `promote_user_to_superuser` | Promote user to admin | `python manage.py promote_user_to_superuser john` |
| `delete_user` | Delete user safely | `python manage.py delete_user --username john` |

---

## Command Aliases

Short versions accepted:
- `--env dev` = `--env development`
- `--env prod` = `--env production`

---

Last Updated: September 30, 2025
