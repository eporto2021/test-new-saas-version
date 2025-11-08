# Product Demo Links Guide

This guide explains how to add "View Demo" buttons to subscription product cards on the "Subscriptions Available" page.

## Overview

The Product Demo Links feature allows you to add clickable demo buttons to each subscription product card. These buttons can link to:
- Video demos (YouTube, Vimeo, etc.)
- Live demo pages
- Product tour pages
- Documentation
- Any other URL you want to showcase

## How It Works

Demo links are managed through the **Django Admin** panel and are stored in the `ProductDemoLink` database table. Each demo link is associated with a specific Stripe Product ID.

## Adding Demo Links

### Via Django Admin (Recommended)

1. **Access Admin Panel**
   - Navigate to `/admin/` in your browser
   - Log in with your admin credentials

2. **Go to Product Demo Links**
   - In the admin sidebar, find **"Subscriptions"** section
   - Click on **"Product Demo Links"**

3. **Add New Demo Link**
   - Click the **"Add Product Demo Link"** button
   - Fill in the form:

#### Form Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Product Name** | Display name of your subscription | "Check each drop off has a pick up" |
| **Stripe Product ID** | Your Stripe product ID from settings.py | `prod_T9FO1AD2u8s2xX` |
| **Demo URL** | Link to demo/video/tour | `https://www.youtube.com/watch?v=abc123` |
| **Button Text** | Text shown on the button | "View Demo" or "Watch Video" |
| **Open in New Tab** | ✓ Opens link in new browser tab | Checked (recommended) |
| **Is Active** | ✓ Show/hide the button | Checked to display |
| **Display Order** | Sort order (lower = first) | 0, 1, 2, etc. |

4. **Save**
   - Click **"Save"** or **"Save and add another"**
   - The demo button will appear immediately on the product card

### Via Django Shell

You can also create demo links programmatically:

```bash
make shell
```

Then in the shell:

```python
from apps.subscriptions.models import ProductDemoLink

# Create a demo link
ProductDemoLink.objects.create(
    product_name='Your Product Name',
    stripe_product_id='prod_T9FO1AD2u8s2xX',
    demo_url='https://www.youtube.com/watch?v=example',
    button_text='View Demo',
    is_active=True,
    open_in_new_tab=True,
    display_order=1
)
```

## How Demo Buttons Appear

### Visual Display

Demo buttons appear at the top of the subscription card footer, above the Subscribe/Request buttons:

```
┌─────────────────────────────────────┐
│ Check each drop off has a pick up   │
│ Automated validation service        │
│                                     │
│ $49.99 / month                      │
│                                     │
│ ✓ Automated validation checks       │
│ ✓ Email notifications               │
│ ✓ Real-time monitoring              │
│                                     │
│ [🎬 View Demo]  ← Purple button     │
│ [Subscribe - $49.99/month]          │
└─────────────────────────────────────┘
```

### Button Styling

- **Color**: Purple/Indigo (`#6366f1`)
- **Icon**: Play circle (🎬)
- **Width**: Full width of card
- **Position**: Above subscribe buttons
- **Hover**: Darkens on hover

## Managing Demo Links

### View All Demo Links

1. Go to `/admin/subscriptions/productdemolink/`
2. You'll see a list with:
   - Product Name
   - Stripe Product ID
   - Demo URL (clickable)
   - Active status
   - Button text
   - Display order
   - Last updated date

### Edit a Demo Link

1. Click on any demo link in the list
2. Update the fields as needed
3. See a **live preview** of how the button will look
4. Save changes

### Preview Feature

The admin panel shows a preview of your demo button:

- ✅/⚠️ Active status badge
- 🔗 New Tab/Same Tab indicator
- Live button preview with your custom text
- Clickable to test the link

### Bulk Actions

Select multiple demo links and use bulk actions:

- **✅ Activate selected demo links** - Turn on multiple buttons
- **⚠️ Deactivate selected demo links** - Turn off multiple buttons

## Finding Your Product IDs

Your Stripe Product IDs are defined in your settings:

### Development

```python
# test/settings.py
ACTIVE_PRODUCTS = [
    'prod_T9FO1AD2u8s2xX',  # Product 1
    'prod_T9G51eeTkn3ttj',  # Product 2
    'prod_T9FPSDcT4R6Ehr',  # Product 3
]
```

### Production

```python
# test/settings_production.py
ACTIVE_PRODUCTS = [
    'prod_LIVE_ABC123',  # Production Product 1
    'prod_LIVE_XYZ789',  # Production Product 2
]
```

## Examples

### Example 1: YouTube Demo Video

```python
ProductDemoLink.objects.create(
    product_name='Role Based Staff Training Website',
    stripe_product_id='prod_T9G51eeTkn3ttj',
    demo_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    button_text='Watch Demo Video',
    is_active=True,
    open_in_new_tab=True,
    display_order=1
)
```

### Example 2: Live Demo Page

```python
ProductDemoLink.objects.create(
    product_name='Load Sheet PDF Creator',
    stripe_product_id='prod_T9FPSDcT4R6Ehr',
    demo_url='https://yourdomain.com/demo/load-sheet',
    button_text='Try Live Demo',
    is_active=True,
    open_in_new_tab=True,
    display_order=2
)
```

### Example 3: Documentation Link

```python
ProductDemoLink.objects.create(
    product_name='API Integration',
    stripe_product_id='prod_ABC123',
    demo_url='https://docs.yourdomain.com/api-guide',
    button_text='View Documentation',
    is_active=True,
    open_in_new_tab=True,
    display_order=3
)
```

## Technical Details

### Database Model

**Table**: `subscriptions_productdemolink`

**Fields**:
- `id` - Auto-increment primary key
- `product_name` - CharField(255)
- `stripe_product_id` - CharField(255, unique=True)
- `demo_url` - URLField(500)
- `is_active` - BooleanField (default: True)
- `button_text` - CharField(50, default: "View Demo")
- `open_in_new_tab` - BooleanField (default: True)
- `display_order` - IntegerField (default: 0)
- `created_at` - DateTimeField (auto_now_add)
- `updated_at` - DateTimeField (auto_now)

### Code Locations

- **Model**: `apps/subscriptions/models.py` (ProductDemoLink class)
- **Admin**: `apps/subscriptions/admin.py` (ProductDemoLinkAdmin)
- **View**: `apps/ecommerce/views.py` (ecommerce_home function)
- **Template**: `templates/ecommerce/components/products_empty.html`
- **Template Filter**: `apps/subscriptions/templatetags/subscription_tags.py` (get_item filter)

### How It's Retrieved

```python
# In ecommerce_home view
from apps.subscriptions.models import ProductDemoLink

demo_links = {}
for product in subscription_products:
    try:
        demo_link = ProductDemoLink.objects.get(
            stripe_product_id=product.product.id,
            is_active=True
        )
        demo_links[product.product.id] = demo_link
    except ProductDemoLink.DoesNotExist:
        pass
```

### Template Usage

```django
{% if demo_links %}
  {% with demo_link=demo_links|get_item:product.product.id %}
    {% if demo_link %}
      <a href="{{ demo_link.demo_url }}" 
         {% if demo_link.open_in_new_tab %}target="_blank"{% endif %}>
        {{ demo_link.button_text }}
      </a>
    {% endif %}
  {% endwith %}
{% endif %}
```

## Troubleshooting

### Demo Button Not Appearing

**Problem**: Button doesn't show on product card

**Solutions**:
1. Verify `is_active` is checked in admin
2. Check `stripe_product_id` matches exactly (case-sensitive)
3. Ensure product is in `ACTIVE_PRODUCTS` list
4. Clear browser cache and refresh page

### Wrong Product Showing Demo

**Problem**: Demo appears on wrong product card

**Solution**: 
- Double-check the `stripe_product_id` in the admin
- Each product ID must be unique (enforced by database)

### Button Styling Issues

**Problem**: Button doesn't look right

**Solution**:
- Clear browser cache
- Check browser console for JavaScript errors
- Ensure Font Awesome icons are loaded

## Best Practices

1. **Use descriptive button text**
   - ✅ "Watch 2-Minute Demo"
   - ✅ "Try Live Demo"
   - ❌ "Click Here"

2. **Always open in new tab**
   - Keeps your site open while user watches demo
   - Prevents losing subscription page

3. **Keep URLs working**
   - Test demo links regularly
   - Update broken links promptly
   - Use URL shorteners for long links

4. **Order logically**
   - Most important demos first (lower display_order)
   - Group related products together

5. **Disable temporarily if needed**
   - Uncheck `is_active` instead of deleting
   - Can re-enable quickly when fixed

## Migration

The migration file is located at:
```
apps/subscriptions/migrations/0004_productdemolink.py
```

This was automatically created and applied when you set up the feature.

## Related Features

- **Product Features List** - See [SUBSCRIPTION_FEATURES_GUIDE.md](SUBSCRIPTION_FEATURES_GUIDE.md)
- **Subscription Requests** - See [SUBSCRIPTION_REQUEST_FEATURE.md](SUBSCRIPTION_REQUEST_FEATURE.md)
- **Product Sync** - See [SUBSCRIPTION_SYNC_GUIDE.md](SUBSCRIPTION_SYNC_GUIDE.md)

## Summary

**Adding a demo link is simple:**

1. Go to Django Admin → Subscriptions → Product Demo Links
2. Click "Add Product Demo Link"
3. Fill in:
   - Product name
   - Stripe Product ID (from settings.py)
   - Demo URL
   - Button text
4. Check "Is Active" and "Open in New Tab"
5. Save

**The demo button appears immediately** on the product card in the "Subscriptions Available" page! 🎉

