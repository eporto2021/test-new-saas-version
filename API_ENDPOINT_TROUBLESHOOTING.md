# API Endpoint Troubleshooting Guide

## Endpoint: `/subscriptions/api/user-services/`

### ✅ Correct URL Format

- **Local:** `http://localhost:8000/subscriptions/api/user-services/`
- **Production:** `https://your-domain.com/subscriptions/api/user-services/`

**Important:** Include the trailing slash `/`

---

### 🔍 Common 404 Causes & Solutions

#### 1. Server Not Restarted
**Problem:** New endpoint not loaded  
**Solution:** 
```bash
# Stop and restart your Django server
# Or if using Docker/Fly.io:
fly deploy  # or fly restart
```

#### 2. Wrong URL
**Problem:** Missing trailing slash or wrong path  
**Solution:** 
- ✅ Correct: `/subscriptions/api/user-services/`
- ❌ Wrong: `/subscriptions/api/user-services` (no trailing slash)
- ❌ Wrong: `/api/user-services/`
- ❌ Wrong: `/subscriptions/user-services/`

#### 3. Missing Authentication
**Problem:** API key not provided  
**Solution:** Include authentication header

```bash
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     http://localhost:8000/subscriptions/api/user-services/
```

---

### 🧪 Testing the Endpoint

#### Step 1: Create an API Key
1. Log in at `/users/profile/`
2. Scroll to "API Keys" section
3. Click "New API Key"
4. **Copy the key immediately** (you won't see it again!)

#### Step 2: Test with curl

```bash
# Replace YOUR_API_KEY with the key you copied
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:8000/subscriptions/api/user-services/
```

#### Step 3: Test with Python

```python
import requests

headers = {
    "Authorization": "Api-Key YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8000/subscriptions/api/user-services/",
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

### 🔐 Authentication Methods

The endpoint accepts authentication via:

1. **API Key Header:**
   ```
   Authorization: Api-Key <your-api-key>
   ```

2. **X-Api-Key Header:**
   ```
   X-Api-Key: <your-api-key>
   ```

3. **Session Cookie:** (if logged into web interface)
   - Just access the URL while logged in

---

### 📋 Expected Responses

#### ✅ Success (200)
```json
{
  "username": "user@example.com",
  "services": [
    {
      "service_id": 1,
      "name": "Service Name",
      "slug": "service-slug",
      "description": "Service description",
      "has_access": true,
      "subscription": {
        "subscription_id": "sub_...",
        "status": "active",
        "current_period_end": "2025-12-25T00:00:00",
        "cancel_at_period_end": false,
        "product_id": "prod_...",
        "product_name": "Service Name"
      }
    }
  ]
}
```

#### ❌ Not Authenticated (401)
```json
{
  "error": "Authentication required"
}
```

#### ❌ Not Found (404)
- Check URL spelling
- Check server is running
- Check Django URL configuration

---

### 🐛 Debugging Steps

1. **Check if endpoint exists:**
   ```bash
   # List all subscription URLs
   python manage.py show_urls | grep subscriptions
   ```

2. **Check server logs:**
   - Look for any errors when accessing the endpoint
   - Check for import errors or exceptions

3. **Test other endpoints:**
   ```bash
   # Test a known working endpoint
   curl http://localhost:8000/subscriptions/api/active-products/
   ```

4. **Verify API key:**
   - Go to `/users/profile/`
   - Check your API keys list
   - Ensure key hasn't been revoked

---

### 💡 Quick Test Script

Save this as `test_endpoint.sh`:

```bash
#!/bin/bash
BASE_URL="${1:-http://localhost:8000}"
API_KEY="${2}"

if [ -z "$API_KEY" ]; then
    echo "Usage: $0 [BASE_URL] [API_KEY]"
    echo "Example: $0 http://localhost:8000 your-api-key-here"
    exit 1
fi

echo "Testing: ${BASE_URL}/subscriptions/api/user-services/"
echo ""

curl -v \
  -H "Authorization: Api-Key ${API_KEY}" \
  -H "Content-Type: application/json" \
  "${BASE_URL}/subscriptions/api/user-services/" \
  | python3 -m json.tool
```

Run it:
```bash
chmod +x test_endpoint.sh
./test_endpoint.sh http://localhost:8000 your-api-key-here
```

---

### 📞 Still Not Working?

1. **Check Django settings:**
   - Ensure `apps.subscriptions` is in `INSTALLED_APPS`
   - Check `ROOT_URLCONF` points to correct urls.py

2. **Check view imports:**
   - Verify `UserServicesList` is in `apps/subscriptions/views/api_views.py`
   - Check `apps/subscriptions/views/__init__.py` imports from `api_views`

3. **Check URL routing:**
   - Verify `apps/subscriptions/urls.py` includes the route
   - Verify `test/urls.py` includes `apps.subscriptions.urls`

4. **Restart everything:**
   - Restart Django development server
   - If using production, restart application servers
   - Clear any caches

