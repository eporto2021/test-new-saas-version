# Demo Request Approval Feature

## Overview

This document explains how the demo request approval system works. When a user requests a demo and an admin approves it in the Django admin interface, two things automatically happen:
1. The demo link becomes visible to the user on the product card
2. An email notification is sent to the user informing them their demo is ready

## How It Works

### User Flow

1. **User Requests Demo**: User clicks "Request Demo" button on product card
2. **Request Created**: System creates a `SubscriptionRequest` with `request_type='demo'` and `status='pending'`
3. **Admin Notification**: Admin receives an email notification about the new demo request
4. **Admin Approves**: Admin marks the request as "Approved" in Django admin
5. **Automatic Actions**:
   - Email sent to user with demo link
   - Demo button becomes visible to user on product card
6. **User Access**: User can now click the demo button to access the demo

### Technical Implementation

#### 1. Models (`apps/subscriptions/models.py`)

**SubscriptionRequest Model**:
- `request_type`: Field that distinguishes between 'subscription' and 'demo' requests
- `status`: Can be 'pending', 'contacted', 'approved', or 'rejected'
- When status changes to 'approved', a signal is triggered

#### 2. Signal Handler (`apps/subscriptions/signals.py`)

**Signal**: `create_availability_on_request_approval`
- Listens to `post_save` signal on `SubscriptionRequest`
- Triggered when a request is saved with `status='approved'`
- Behavior depends on `request_type`:
  - **Demo requests**: Calls `_send_demo_approval_email()` to send notification
  - **Subscription requests**: Creates `SubscriptionAvailability` to enable Subscribe button

**Email Function**: `_send_demo_approval_email()`
- Sends personalized email to user
- Includes direct demo link if available
- Gracefully handles cases where demo link doesn't exist
- Logs success/failure for monitoring

#### 3. Template Tags (`apps/subscriptions/templatetags/subscription_tags.py`)

**New Template Tag**: `user_has_approved_demo`
```python
{% user_has_approved_demo user product.product.id as has_approved_demo %}
```
- Returns `True` if user has an approved demo request for the product
- Used to control demo button visibility

**Existing Tags Used**:
- `user_has_requested_demo`: Check if user has requested demo (any status)
- `get_item`: Helper to retrieve demo link from dictionary

#### 4. Template (`templates/ecommerce/components/products_empty.html`)

Demo button visibility logic:
```django
{% if has_approved_demo and demo_links %}
  {% with demo_link=demo_links|get_item:product.product.id %}
    <!-- Show demo button -->
  {% endwith %}
{% endif %}
```

#### 5. Admin Interface (`apps/subscriptions/admin.py`)

**Enhanced Features**:
- `request_type_display`: Shows request type with icons (🎬 for demo, 📦 for subscription)
- Added `request_type` filter to easily filter demo vs subscription requests
- Updated fieldsets to include `request_type` field

**Admin Actions**:
1. **✅ Approve all requests**: Approves both subscription and demo requests
2. **📦 Approve subscription requests**: Approves only subscription requests in selection
3. **🎬 Approve demo requests**: Approves only demo requests and sends emails
4. **📞 Mark as contacted**: Change status to "contacted"
5. **❌ Reject requests**: Change status to "rejected"

## Usage

### For Admins

#### Approving a Single Demo Request

1. Navigate to Django Admin → Subscriptions → Subscription Requests
2. Click on the demo request to open it
3. Change `Status` field to "Approved"
4. Click "Save"
5. System automatically:
   - Sends email to user
   - Enables demo button for user

#### Bulk Approving Demo Requests

1. Navigate to Django Admin → Subscriptions → Subscription Requests
2. Filter by `Request type: Demo Request` (optional but recommended)
3. Select the demo requests you want to approve
4. Choose "🎬 Approve demo requests" from the action dropdown
5. Click "Go"
6. Confirmation message shows how many emails were sent

### For Users

#### Requesting a Demo

1. Browse available subscription products
2. Click "Request Demo" button on product card
3. Confirmation message appears: "Demo Request Submitted"
4. Wait for approval notification email

#### Accessing Approved Demo

1. Receive email notification when demo is approved
2. Visit dashboard/ecommerce page
3. Demo button appears on product card (purple "View Demo" button)
4. Click demo button to access demo in new tab

## Email Template

### Subject
```
Your {Product Name} Demo is Ready!
```

### Body (with demo link)
```
Hi {User Name},

Great news! Your demo request for {Product Name} has been approved.

You can now access the product demo at any time by visiting your dashboard. 
Look for the "{Product Name}" card and click the demo button.

Direct demo link: {Demo URL}

If you have any questions or need additional assistance, please don't hesitate 
to reach out to our support team at {support email}.

Best regards,
The {Platform Name} Team
```

### Body (without demo link)
```
Hi {User Name},

Great news! Your demo request for {Product Name} has been approved.

Our team will be in touch shortly with access details and next steps.

If you have any questions, please reach out to our support team at {support email}.

Best regards,
The {Platform Name} Team
```

## Configuration

### Required Settings

1. **Email Backend** (configured in `test/settings.py` or `test/settings_production.py`)
   ```python
   # Development
   EMAIL_BACKEND = 'apps.utils.email_backend.PrintEmailBackend'
   
   # Production
   EMAIL_BACKEND = "anymail.backends.mailersend.EmailBackend"
   ```

2. **Project Metadata** (for email personalization)
   ```python
   PROJECT_METADATA = {
       'NAME': 'Your Platform Name',
       'CONTACT_EMAIL': 'support@yourplatform.com',
   }
   ```

3. **Default From Email**
   ```python
   DEFAULT_FROM_EMAIL = "noreply@yourplatform.com"
   ```

### Setting Up Demo Links

For the demo button to appear after approval, you must create a `ProductDemoLink`:

1. Navigate to Django Admin → Subscriptions → Product Demo Links
2. Click "Add Product Demo Link"
3. Fill in:
   - **Product name**: Name of the subscription product
   - **Stripe product ID**: The Stripe Product ID (e.g., `prod_ABC123`)
   - **Demo URL**: Full URL to the demo (e.g., `https://yoursite.com/demo/product`)
   - **Button text**: Text to display (default: "View Demo")
   - **Is active**: ✓ (checked)
   - **Open in new tab**: ✓ (recommended)
4. Click "Save"

## Testing

### Test the Complete Flow

1. **Create Demo Request**:
   ```bash
   # As a logged-in user
   POST /subscriptions/request-demo/{product_id}/
   ```

2. **Verify Request Created**:
   - Check Django Admin → Subscription Requests
   - Should see new request with Type: 🎬 Demo, Status: ⏳ Pending

3. **Approve Request**:
   - Change status to "Approved" and save
   - OR use "🎬 Approve demo requests" action

4. **Check Email Sent**:
   - Development: Check console output
   - Production: Check MailerSend dashboard or user's inbox

5. **Verify Demo Button Visible**:
   - Log in as the user
   - Navigate to ecommerce page
   - Demo button should appear on product card

### Manual Testing Checklist

- [ ] User can request demo
- [ ] Admin receives notification email
- [ ] Admin can filter demo requests
- [ ] Admin can approve demo request
- [ ] User receives approval email
- [ ] Demo button appears for user
- [ ] Demo link opens correctly
- [ ] Only approved users see demo button
- [ ] Email includes correct demo URL
- [ ] Email personalizes with user's name

## Troubleshooting

### Demo Button Not Appearing After Approval

**Possible Causes**:
1. ProductDemoLink not created or inactive
   - Solution: Create/activate ProductDemoLink in admin
2. Stripe Product ID mismatch
   - Solution: Verify exact Product ID match
3. User needs to refresh page
   - Solution: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Email Not Being Sent

**Possible Causes**:
1. Email backend not configured
   - Check `EMAIL_BACKEND` setting
2. MailerSend API key missing (production)
   - Set `MAILERSEND_API_KEY` environment variable
3. Signal not triggering
   - Check logs for errors in signal handler
   - Verify `request_type='demo'` on the request

**Check Logs**:
```bash
# Check for signal execution
grep "Demo approval email sent" logs/
grep "Failed to send demo approval email" logs/
```

### User Receives Email But No Demo Button

**Cause**: ProductDemoLink doesn't exist for this product

**Solution**:
1. Create ProductDemoLink in admin
2. Ensure `stripe_product_id` matches exactly
3. Set `is_active=True`

## Database Queries

### Find All Approved Demo Requests
```python
from apps.subscriptions.models import SubscriptionRequest

approved_demos = SubscriptionRequest.objects.filter(
    request_type='demo',
    status='approved'
)
```

### Find Users with Approved Demos for Specific Product
```python
approved_users = SubscriptionRequest.objects.filter(
    request_type='demo',
    status='approved',
    product_stripe_id='prod_ABC123'
).values_list('user__email', flat=True)
```

### Count Demo Requests by Status
```python
from django.db.models import Count

SubscriptionRequest.objects.filter(
    request_type='demo'
).values('status').annotate(count=Count('id'))
```

## Related Files

- **Models**: `apps/subscriptions/models.py`
- **Signals**: `apps/subscriptions/signals.py`
- **Admin**: `apps/subscriptions/admin.py`
- **Views**: `apps/subscriptions/views/views.py`
- **Template Tags**: `apps/subscriptions/templatetags/subscription_tags.py`
- **Template**: `templates/ecommerce/components/products_empty.html`
- **URLs**: `apps/subscriptions/urls.py`

## Future Enhancements

Possible improvements to consider:
1. HTML email template with better formatting
2. Automatic demo link expiration after X days
3. Demo usage analytics tracking
4. Reminder emails if user doesn't access demo
5. Demo access revocation from admin
6. Custom demo duration limits per product
7. Demo access logs/audit trail

