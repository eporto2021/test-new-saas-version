# User Programs Directory

This directory contains user-specific programs, templates, and configurations for each product/service. This data is stored **outside the media folder** for security reasons since media folders are typically web-accessible.

## 🔒 Security Benefits

- ✅ **Not Web-Accessible** - Unlike `media/`, this folder is not served directly via URLs
- ✅ **Application-Level Access** - Only Django can access these files
- ✅ **Protected Templates** - User templates are served through Django's template system
- ✅ **Secure Storage** - Cloud Function URLs and configs are not publicly accessible

## 📁 Directory Structure

```
user_programs/
└── user_{id}/
    └── {product_name}/
        ├── template.html              # User's custom UI template (Django template)
        ├── cloud_function_url.txt     # URL to user's Cloud Function
        ├── config.json                # User-specific configuration
        ├── uploads/                   # User's uploaded files
        │   └── *.xlsx, *.csv, etc.
        └── processed/                 # Processed/output files
            └── result_*.csv
```

## 📂 Example Structure

```
user_programs/
└── user_18/
    └── check-every-drop-off-has-a-pick-up/
        ├── template.html              # Custom UI for user 18
        ├── cloud_function_url.txt     # Their Cloud Function endpoint
        ├── config.json                # Their custom settings
        ├── uploads/                   # Their uploaded data files
        └── processed/                 # Their processed results
```

## 📝 File Descriptions

### template.html
Custom Django template with user-specific UI and JavaScript. This template is included in the subscription service page.

**Location:** `user_programs/user_{id}/{product_name}/template.html`

**Features:**
- Custom forms and UI elements
- JavaScript to call Cloud Functions
- Display logic for results
- User-specific styling

**Security:** Rendered through Django's template system, not directly accessible via URL.

### cloud_function_url.txt
Plain text file containing the URL to the user's deployed Cloud Function.

**Example content:**
```
https://us-central1-project-id.cloudfunctions.net/process-user18
```

**Security:** Not web-accessible, only read by Django backend.

### config.json
JSON configuration file for user-specific settings.

**Example content:**
```json
{
  "max_file_size_mb": 10,
  "allowed_file_types": ["csv", "xlsx"],
  "custom_settings": {
    "validation_rules": {
      "check_duplicates": true
    }
  }
}
```

**Security:** Protected from direct access, only parsed by application code.

### uploads/
Directory where user's uploaded files are stored.

**Security:** Files are stored in application directory, not directly web-accessible. Access controlled through Django views.

### processed/
Directory where processed/output files are stored.

**Security:** Similar to uploads/, only accessible through authenticated Django views.

---

## 🚀 Setup for New User

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

# Edit the template as needed
nano "user_programs/user_${USER_ID}/${PRODUCT_NAME}/template.html"
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

### Step 5: Set Permissions
```bash
# Ensure Django can read/write
chmod -R 755 "user_programs/user_${USER_ID}"
chmod 644 "user_programs/user_${USER_ID}/${PRODUCT_NAME}"/*.{html,txt,json}
```

---

## 🔧 How It Works

1. **User subscribes** to a product (e.g., "check-every-drop-off-has-a-pick-up")
2. **User accesses** `/subscriptions/service/check-every-drop-off-has-a-pick-up/`
3. **Django loads** their custom template from `user_programs/user_{id}/{product_name}/template.html`
4. **Template displays** their unique UI with access to:
   - `{{ cloud_function_url }}` - Their Cloud Function endpoint
   - `{{ upload_directory }}` - Their upload path
   - `{{ processed_directory }}` - Their processed files path
   - `{{ user }}` - User object with user info
5. **JavaScript calls** the Cloud Function URL for custom processing
6. **Results are saved** in their `processed/` directory
7. **Access is controlled** through Django views (authentication required)

---

## 🔐 Security Features

### 1. Not Web-Accessible
Unlike `media/` folder which is typically served directly by web servers, `user_programs/` is only accessible through Django's application logic.

### 2. Template Security
Templates are rendered through Django's template system which:
- Prevents arbitrary code execution
- Escapes dangerous HTML/JavaScript automatically
- Provides safe template language only

### 3. File Access Control
All file access goes through Django views which can:
- Verify user authentication
- Check permissions
- Log access attempts
- Validate file types and sizes

### 4. Isolated User Data
Each user has their own directory, preventing:
- Cross-user data access
- File name collisions
- Data leakage between users

---

## 📊 Accessing User Data in Code

### In Views (`views.py`)
```python
# Get user's template path
template_path = get_user_template_path(user, product_name)

# Get user's Cloud Function URL
cf_url = get_user_cloud_function_url(user, product_name)

# Get upload directory
upload_dir = get_user_upload_directory(user, product_name)

# Get processed directory
processed_dir = get_user_processed_directory(user, product_name)
```

### In Templates
```django
{# Cloud Function URL #}
<script>
  const cloudFunctionUrl = '{{ cloud_function_url }}';
</script>

{# Upload directory (for display/info only) #}
<p>Your files: {{ upload_directory }}</p>

{# User info #}
<p>Welcome, {{ user.get_full_name }}!</p>
```

---

## 📋 Best Practices

### ✅ DO:
- Keep sensitive config files (Cloud Function URLs, API keys) in `config.json`
- Use meaningful product names in directory structure
- Set appropriate file permissions (644 for files, 755 for directories)
- Regularly backup user programs
- Monitor disk space usage
- Validate all file uploads
- Log access to user files

### ❌ DON'T:
- Don't store executable Python files here (use Cloud Functions instead)
- Don't commit user data to version control (see `.gitignore`)
- Don't make this directory web-accessible
- Don't share Cloud Function URLs publicly
- Don't skip authentication checks when accessing files

---

## 🧹 Maintenance

### Cleanup Old Files
```bash
# Remove uploads older than 30 days
find user_programs/*/*/uploads -type f -mtime +30 -delete

# Remove processed files older than 90 days
find user_programs/*/*/processed -type f -mtime +90 -delete
```

### Check Disk Usage
```bash
# Size of all user programs
du -sh user_programs/

# Size per user
du -sh user_programs/user_*

# Largest directories
du -sh user_programs/*/* | sort -hr | head -10
```

### Backup User Programs
```bash
# Backup all user programs
tar -czf user_programs_backup_$(date +%Y%m%d).tar.gz user_programs/

# Backup specific user
tar -czf user_18_backup_$(date +%Y%m%d).tar.gz user_programs/user_18/
```

---

## 🔍 Troubleshooting

### Template Not Loading
**Error:** Template not found

**Solutions:**
1. Verify file exists: `user_programs/user_{id}/{product_name}/template.html`
2. Check file permissions (should be readable by Django process)
3. Verify `user_programs/` is in `TEMPLATES['DIRS']` in settings.py
4. Falls back to `templates/subscriptions/file_upload_service_example.html` if custom doesn't exist

### Cloud Function URL Not Found
**Problem:** `cloud_function_url` is None in template

**Solutions:**
1. Verify `cloud_function_url.txt` exists
2. Check file contains valid URL (no extra whitespace)
3. Ensure file is readable
4. Check function returns correct path

### Permission Denied
**Error:** Cannot read/write files

**Solutions:**
```bash
# Fix permissions
chmod -R 755 user_programs/
chmod 644 user_programs/*/*/*.{html,txt,json}
chmod 775 user_programs/*/*/{uploads,processed}

# Check ownership
ls -la user_programs/user_18/
```

---

## 📚 Related Files

- **Settings:** `test/settings.py` - TEMPLATES['DIRS'] includes `user_programs/`
- **Views:** `apps/subscriptions/views/views.py` - Helper functions for user programs
- **Template:** `templates/subscriptions/subscription_service.html` - Includes user template
- **Documentation:** `USER_TEMPLATE_STRUCTURE.md` - Overall implementation guide

---

## 🎯 Summary

The `user_programs/` directory provides a **secure, isolated, and flexible** way to store user-specific programs and data:

- 🔒 **Secure** - Not web-accessible, application-controlled access only
- 👤 **Isolated** - Each user has their own directory
- 🎨 **Flexible** - Custom templates and logic per user
- 📊 **Organized** - Clear structure for templates, configs, and data
- 🚀 **Scalable** - Easy to add new users and products

This approach gives you the security benefits of application-level access control while maintaining the flexibility to customize each user's experience!

