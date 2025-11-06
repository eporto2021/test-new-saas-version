# User-Specific Template Structure

## ✅ Changes Made

### 1. **New Directory Structure**
Changed from flat structure to organized, user-specific directories stored **outside media/** for security:

**Before:**
```
media/
└── user_templates/
    └── user_18/
        └── check-every-drop-off-has-a-pick-up.html
```

**After:**
```
user_programs/                              # ← Application folder, NOT media
└── user_18/
    └── check-every-drop-off-has-a-pick-up/
        ├── template.html              # Custom UI
        ├── cloud_function_url.txt     # Cloud Function endpoint
        ├── config.json                # User settings
        ├── uploads/                   # Uploaded files
        └── processed/                 # Processed results
```

**Security Benefits:**
- ✅ Not web-accessible (unlike media folder)
- ✅ Application-level access control only
- ✅ Protected from direct URL access

### 2. **Updated Django Settings**
Added `user_programs/` to template directories in `test/settings.py`:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "user_programs",  # ← Added this (NOT media)
        ],
        # ...
    },
]
```

### 3. **Updated Views** (`apps/subscriptions/views/views.py`)

Added helper functions:
- `get_user_template_path(user, product_name)` - Returns path to user's custom template
- `get_user_cloud_function_url(user, product_name)` - Returns user's Cloud Function URL
- `get_user_upload_directory(user, product_name)` - Returns upload directory path
- `get_user_processed_directory(user, product_name)` - Returns processed files directory path

Updated `subscription_service` view to pass these to the template context:
```python
context = {
    # ... existing context ...
    'user_template_path': user_template_path,
    'cloud_function_url': cloud_function_url,
    'upload_directory': upload_directory,
    'processed_directory': processed_directory,
}
```

### 4. **Created Fallback Template**
Created `templates/subscriptions/file_upload_service_example.html` as the default template when user doesn't have a custom one.

---

## 📁 Directory Structure Details

### For Each User + Product Combination:
```
user_programs/user_{id}/{product_name}/
```

### Example for User 18, Product "check-every-drop-off-has-a-pick-up":
```
user_programs/user_18/check-every-drop-off-has-a-pick-up/
├── template.html              
├── cloud_function_url.txt     
├── config.json                
├── uploads/                   
└── processed/                 
```

---

## 🔧 How It Works

### 1. **User subscribes to a product**
When user 18 subscribes to "check-every-drop-off-has-a-pick-up", they visit:
```
/subscriptions/service/check-every-drop-off-has-a-pick-up/
```

### 2. **Django loads user-specific template**
The view calls:
```python
user_template_path = get_user_template_path(request.user, product.name)
# Returns: "user_programs/user_18/check-every-drop-off-has-a-pick-up/template.html"
```

### 3. **Template is included in the page**
In `subscription_service.html`:
```django
{% include user_template_path %}
```

### 4. **Template has access to:**
- `{{ user }}` - Current user object
- `{{ cloud_function_url }}` - User's custom Cloud Function URL
- `{{ upload_directory }}` - Where their files are uploaded
- `{{ processed_directory }}` - Where processed files are saved
- `{{ service_slug }}` - Service identifier
- `{{ product }}` - Product object

### 5. **Template can call Cloud Function**
JavaScript in the template can call the user's custom Cloud Function:
```javascript
const cloudFunctionUrl = '{{ cloud_function_url }}';
const response = await fetch(cloudFunctionUrl, {
  method: 'POST',
  body: JSON.stringify({ /* user data */ })
});
```

---

## 🎯 Benefits of This Approach

### ✅ Security
- No Python code execution in media folder
- Cloud Functions run in isolated environments
- Each user's data is separated
- Templates use safe Django template language only

### ✅ Flexibility
- Each user can have completely different UI for the same product
- Each user can have their own Cloud Function with custom logic
- Easy to customize per-user settings via `config.json`

### ✅ Scalability
- Cloud Functions auto-scale
- No complex code management in Django
- Easy to add new users (just create a directory)

### ✅ Maintainability
- Clear directory structure
- User data isolated
- Easy to debug (one directory per user/product)

---

## 🚀 Setting Up a New User

### Step 1: Create Directory Structure
```bash
USER_ID=25
PRODUCT_NAME="check-every-drop-off-has-a-pick-up"

mkdir -p "user_programs/user_${USER_ID}/${PRODUCT_NAME}/{uploads,processed}"
```

### Step 2: Create Template
```bash
# Copy from default template
cp templates/subscriptions/file_upload_service_example.html \
   "user_programs/user_${USER_ID}/${PRODUCT_NAME}/template.html"

# Or copy from another user
cp "user_programs/user_18/${PRODUCT_NAME}/template.html" \
   "user_programs/user_${USER_ID}/${PRODUCT_NAME}/template.html"
```

### Step 3: Set Cloud Function URL
```bash
echo "https://us-central1-project.cloudfunctions.net/check-drop-off-user25" > \
  "user_programs/user_${USER_ID}/${PRODUCT_NAME}/cloud_function_url.txt"
```

### Step 4: Create Config (Optional)
```bash
cat > "user_programs/user_${USER_ID}/${PRODUCT_NAME}/config.json" << 'EOF'
{
  "max_file_size_mb": 10,
  "allowed_file_types": ["csv", "xlsx", "xls"],
  "custom_settings": {
    "validation_rules": {
      "check_duplicates": true
    }
  }
}
EOF
```

### Step 5: Deploy User's Cloud Function
```bash
# In your cloud_functions directory
cd apps/services/cloud_functions/

# Deploy for user 25
gcloud functions deploy check-drop-off-user25 \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point process
```

---

## 📝 Example Cloud Function (Python)

```python
# cloud_function/main.py
import functions_framework
from google.cloud import storage
import json

@functions_framework.http
def process(request):
    """User-specific processing logic"""
    
    # Enable CORS
    if request.method == 'OPTIONS':
        return ('', 204, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    
    # Parse request
    request_json = request.get_json()
    user_id = request_json.get('user_id')
    upload_dir = request_json.get('upload_directory')
    processed_dir = request_json.get('processed_directory')
    
    # YOUR CUSTOM LOGIC HERE
    # Example: Process uploaded file
    result_data = {
        'status': 'success',
        'message': 'Processing complete',
        'processed_rows': 100,
    }
    
    # Generate signed URL for result file
    # Note: processed_dir is like "user_programs/user_18/.../processed/"
    storage_client = storage.Client()
    bucket = storage_client.bucket('your-bucket')
    blob = bucket.blob(f'{processed_dir}result_{user_id}.csv')
    
    # Upload result
    blob.upload_from_string('col1,col2\nval1,val2')
    
    # Generate temporary URL (1 hour expiry)
    url = blob.generate_signed_url(
        version='v4',
        expiration=3600,
        method='GET'
    )
    
    result_data['url'] = url
    
    return (json.dumps(result_data), 200, {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    })
```

---

## 🔍 Troubleshooting

### Template Not Loading
**Error:** `TemplateDoesNotExist at /subscriptions/service/xxx/`

**Solutions:**
1. Check product name matches exactly (case-sensitive)
2. Verify file exists: `user_programs/user_{id}/{product_name}/template.html`
3. Check `user_programs/` is in `TEMPLATES['DIRS']` in settings.py
4. Falls back to `templates/subscriptions/file_upload_service_example.html` if custom doesn't exist

### Cloud Function Not Called
**Problem:** JavaScript not executing

**Solutions:**
1. Verify `cloud_function_url.txt` exists and contains valid URL
2. Check browser console for errors
3. Ensure CORS is enabled on Cloud Function
4. Check Cloud Function logs in GCP console

### Files Not Uploading
**Problem:** Upload directory not found

**Solutions:**
1. Ensure `uploads/` directory exists
2. Check file permissions
3. Verify Django has write access to `media/user_data/`

---

## 📚 Additional Resources

- See `user_programs/README.md` for detailed directory documentation and security info
- Example template: `user_programs/user_18/check-every-drop-off-has-a-pick-up/template.html`
- Helper functions: `apps/subscriptions/views/views.py` (lines 291-336)
- .gitignore: `user_programs/.gitignore` - Protects user data from being committed

---

## 🎉 Summary

You now have a flexible, secure, and scalable system where:
- ✅ Each user can have custom UI/logic for the same product
- ✅ User data is isolated and private
- ✅ Custom processing happens in Cloud Functions
- ✅ Easy to add new users and products
- ✅ No security risks from executing user code

The structure supports your requirement: **"each user will have differing logic"** by giving each user their own template and Cloud Function!

