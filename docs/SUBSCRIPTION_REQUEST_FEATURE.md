# Subscription Request Feature

## Overview

Users can now request subscriptions by clicking a "Request Subscription" button on each product card. When clicked, admins receive an email notification.

## How It Works

### User Flow

1. User goes to **"Subscriptions Available"** tab (`/ecommerce/`)
2. User sees subscription products with a green **"Request Subscription"** button
3. User clicks the button
4. System creates a `SubscriptionRequest` record
5. Admin receives email notification
6. User sees success message: "Your subscription request has been submitted! We'll contact you shortly to set up your trial."

### Admin Flow

1. Admin receives email with:
   - User email
   - User name
   - Product name
   - Product ID
   - Request date
   - Link to view request in admin panel

2. Admin views request in Django admin at `/admin/subscriptions/subscriptionrequest/`
3. Admin can update status: Pending → Contacted → Approved/Rejected
4. Admin can add internal notes

## Files Created/Modified

### Models
**File:** `apps/subscriptions/models.py`

```python
class SubscriptionRequest(models.Model):
    user = ForeignKey(CustomUser)
    product_name = CharField
    product_stripe_id = CharField
    message = TextField (optional)
    status = CharField (pending/contacted/approved/rejected)
    created_at = DateTimeField
    updated_at = DateTimeField
    admin_notes = TextField
```

### Views
**File:** `apps/subscriptions/views/views.py`

```python
@login_required
def request_subscription(request, product_id):
    # Creates SubscriptionRequest
    # Sends email to admins
    # Shows success message
```

### URLs
**File:** `apps/subscriptions/urls.py`

```python
path("request/<str:product_id>/", views.request_subscription, name="request_subscription")
```

### Admin
**File:** `apps/subscriptions/admin.py` (NEW)

Admin interface with:
- List view with filters
- Status management
- Bulk actions (mark contacted, approved, rejected)
- User profile links

### Template
**File:** `templates/ecommerce/components/products_empty.html`

Added green "Request Subscription" button above existing subscribe buttons.

## Email Configuration

### Development
Emails are printed to the console (Docker logs):

```bash
docker logs test-new-saas-version-web-1
```

### Production
Configure in `test/settings_production.py` or environment variables:

```python
# Example: Using Mailgun
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
}
```

Or use other providers:
- Gmail
- SendGrid
- Amazon SES
- Postmark

## Email Recipients

Emails are sent to admins defined in settings:

**File:** `test/settings.py` (line 467)
```python
ADMINS = [("Max", "maxdavenport96@gmail.com")]
```

To add more admins:
```python
ADMINS = [
    ("Max", "maxdavenport96@gmail.com"),
    ("Admin 2", "admin2@example.com"),
    ("Support", "support@example.com"),
]
```

## Email Content Example

```
Subject: New Subscription Request: Starter Package

User: user@example.com
Name: John Doe
Product: Starter Package
Product ID: prod_T3u59Bp4A9Vafm
Request Date: 2025-09-30 14:30:00

Message from user:
I'm interested in trying this for my business.

View in admin: http://localhost:8000/admin/subscriptions/subscriptionrequest/change/1/
```

## Admin Panel Features

### View Requests
Navigate to: `/admin/subscriptions/subscriptionrequest/`

### Filter By:
- Status (pending, contacted, approved, rejected)
- Created date

### Search By:
- User email
- User name
- Product name

### Bulk Actions:
- Mark as contacted
- Mark as approved
- Mark as rejected

### Individual Request View:
- User information
- Product details
- Request message
- Status dropdown
- Admin notes field
- Timestamps

## Button Styling

The "Request Subscription" button:
- **Color**: Green (`#10b981`)
- **Hover**: Darker green (`#059669`)
- **Icon**: Paper plane icon
- **Position**: Top of card footer (above subscribe buttons)
- **Full width**: Takes up 100% of card width

## Testing

### 1. View in Development

1. Go to http://localhost:8000/ecommerce/
2. See subscription products
3. Click "Request Subscription" on any product
4. Check Docker logs for email:

```bash
docker logs test-new-saas-version-web-1 | grep "New Subscription Request"
```

### 2. View in Admin

1. Go to http://localhost:8000/admin/
2. Navigate to Subscriptions → Subscription requests
3. See all requests with status

### 3. Check Email (Development)

```bash
# Watch Docker logs in real-time
docker logs -f test-new-saas-version-web-1

# Then click "Request Subscription" button
# You'll see the email printed in the logs
```

## Customization

### Change Button Text

Edit `templates/ecommerce/components/products_empty.html` line 56:

```html
{% translate "Request Subscription" %}
<!-- Change to -->
{% translate "Request Trial" %}
<!-- or -->
{% translate "Contact Sales" %}
```

### Change Button Color

Edit line 52:

```html
background: #10b981;  <!-- Green -->
<!-- Change to: -->
background: #3b82f6;  <!-- Blue -->
background: #8b5cf6;  <!-- Purple -->
background: #f59e0b;  <!-- Orange -->
```

### Add Message Field

Update the template to include a textarea:

```html
<form action="{% url 'subscriptions:request_subscription' product.product.id %}" method="POST">
  {% csrf_token %}
  <textarea name="message" placeholder="Tell us about your needs..." 
            class="w-full p-2 border rounded mb-2"></textarea>
  <button type="submit">Request Subscription</button>
</form>
```

### Customize Email Template

Edit the email content in `apps/subscriptions/views/views.py` lines 299-311.

## Security

- ✅ Login required (`@login_required`)
- ✅ POST method only (`@require_http_methods(["POST"])`)
- ✅ CSRF protection (Django's `{% csrf_token %}`)
- ✅ Product validation (404 if product doesn't exist)
- ✅ Error handling and logging

## Future Enhancements

Possible improvements:
- [ ] Add email confirmation to user after request
- [ ] Add Slack/Discord notifications
- [ ] Create automatic trial provisioning
- [ ] Add request limits (e.g., 1 request per product per user)
- [ ] Add rich text editor for admin responses
- [ ] Send status update emails when request changes

## Troubleshooting

### Button not appearing?
- Check that you're on the ecommerce page with no products purchased
- Verify `subscription_products` is being passed to template

### Email not sending?
- Check `EMAIL_BACKEND` in settings
- View Docker logs: `docker logs test-new-saas-version-web-1`
- Verify `ADMINS` list is not empty

### Request not saving?
- Check migrations ran successfully
- Check for errors in Django logs
- Verify user is authenticated

## Production Setup

Before going live:

1. **Configure Email Provider**:
   ```python
   # In settings_production.py
   EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
   ```

2. **Set ADMINS**:
   ```python
   ADMINS = [
       ("Support Team", "support@yourdomain.com"),
       ("Sales", "sales@yourdomain.com"),
   ]
   ```

3. **Test Email**:
   ```bash
   python manage.py sendtestemail admin@example.com
   ```

## Database Schema

```sql
CREATE TABLE subscriptions_subscriptionrequest (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users_customuser(id),
    product_name VARCHAR(255),
    product_stripe_id VARCHAR(255),
    message TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    admin_notes TEXT
);
```

## Related Files

- `apps/subscriptions/models.py` - SubscriptionRequest model
- `apps/subscriptions/views/views.py` - request_subscription view
- `apps/subscriptions/urls.py` - URL routing
- `apps/subscriptions/admin.py` - Admin interface
- `templates/ecommerce/components/products_empty.html` - Button UI
- `test/settings.py` - Email & admin configuration
