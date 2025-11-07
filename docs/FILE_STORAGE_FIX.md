# File Storage Error Fix Guide

## Problem

Users are experiencing file processing errors in production with messages like:

```
[Errno 2] No such file or directory: '/data/media/user_data/user_9/2025/11/07/RUN_SHEET_Sunday_2nd_November_Formatted.xlsx'
```

This occurs when:
1. File records exist in the database
2. But the actual files are missing from storage (the `/data/media` volume)

## Common Causes

1. **Files uploaded before volume was properly configured** - The volume wasn't mounted or writable when files were uploaded
2. **Volume not persisted** - Files were uploaded to ephemeral storage and lost during deployment
3. **Storage path mismatch** - Files were uploaded to one location but code is looking in another
4. **Manual file deletion** - Files were accidentally deleted from the volume

## Solution

### Step 1: Verify Volume Configuration

First, ensure your Fly.io volume is properly configured and mounted:

```bash
# Check if volume exists
fly volumes list -a test-blue-smoke-97

# SSH into the app and check the mount
fly ssh console -a test-blue-smoke-97
ls -la /data/media/
exit
```

Expected output: You should see the `user_data/` directory in `/data/media/`

If the volume doesn't exist or isn't mounted:
1. Create volume: `fly volumes create data --size 10 --region syd -a test-blue-smoke-97`
2. Ensure `fly.toml` has the mount configuration (already done)
3. Deploy: `fly deploy -a test-blue-smoke-97`

### Step 2: Check for Missing Files

Run the diagnostic command to identify missing files:

```bash
# In production (via SSH)
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files"

# Check for a specific user
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --user-id 9"
```

This will show:
- How many files are in the database
- Which files are missing from storage
- File IDs, names, and paths

Example output:
```
Checking all files...
Total file records in database: 15

✗ Found 3 missing files:

User 9: 3 missing file(s)
  - ID 42: RUN_SHEET_Sunday_2nd_November_Formatted.xlsx (status=pending, reason=File not in storage)
    Path: user_data/user_9/2025/11/07/RUN_SHEET_Sunday_2nd_November_Formatted.xlsx
```

### Step 3: Fix Missing File Records

You have two options:

#### Option A: Mark as Failed (Recommended)

This updates the file status to 'failed' and adds a user-friendly message:

```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --fix"
```

This will:
- Update file status to 'failed'
- Add a log message: "File missing from storage. Please re-upload your file."
- Users will see this message in the UI and can re-upload

#### Option B: Delete Records (Destructive)

Only use this if you want to completely remove the records:

```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --delete"
```

⚠️ **Warning**: This permanently deletes database records. You'll need to confirm by typing 'yes'.

### Step 4: Ask Users to Re-upload

After marking files as failed:
1. Users will see the failed status in their dashboard
2. The processing log will say "Please re-upload your file"
3. They can upload the file again and it will work correctly

## Prevention

The code has been updated with the following improvements:

### 1. Storage Backend Compatibility
- Uses `default_storage.exists()` to check if files exist
- Uses `file.open('rb')` instead of accessing `.path` directly
- Works with any Django storage backend (local, S3, etc.)

### 2. Early Validation
- Checks file existence before starting batch processing
- Provides clear error messages about missing files
- Prevents wasted processing time

### 3. Better Error Handling
- Separate handling for `FileNotFoundError` vs other errors
- Detailed logging with file IDs and paths
- User-friendly error messages in processing logs

### 4. Temporary File Management
- Creates temp copies for processing (works with any storage)
- Properly cleans up temp files even on errors
- Uses context managers and try/finally blocks

## Testing in Development

To test the fix locally:

```bash
# Check for missing files
python manage.py check_missing_files

# Simulate a missing file by moving one
mv media/user_data/user_1/some_file.xlsx /tmp/
python manage.py check_missing_files --user-id 1

# Mark as failed
python manage.py check_missing_files --user-id 1 --fix

# Restore the file for testing
mv /tmp/some_file.xlsx media/user_data/user_1/
```

## Code Changes Made

### 1. `apps/services/tasks.py`

#### `process_data_file()` function:
- ✅ Added file existence check with `default_storage.exists()`
- ✅ Creates temporary copy of file for processing
- ✅ Works with any storage backend (not just local filesystem)
- ✅ Proper cleanup with try/finally blocks

#### `_call_user_batch_processor()` function:
- ✅ Validates each file exists before processing
- ✅ Skips files with no file field
- ✅ Raises clear error if files are missing
- ✅ Cleans up temp files on errors

#### `process_all_user_files()` task:
- ✅ Checks all files before starting batch processing
- ✅ Lists missing files in error message
- ✅ Separate exception handler for `FileNotFoundError`
- ✅ User-friendly error messages in processing logs

### 2. New Management Command

`apps/services/management/commands/check_missing_files.py`:
- ✅ Scans all UserDataFile records
- ✅ Checks if files exist in storage
- ✅ Groups results by user
- ✅ Can mark files as failed (`--fix`)
- ✅ Can delete orphaned records (`--delete`)

## Monitoring

Add these checks to your monitoring:

```bash
# Cron job to check for missing files weekly
0 2 * * 1 python manage.py check_missing_files --fix
```

Or set up alerts:
```python
# In your monitoring code
from apps.services.models import UserDataFile
from django.core.files.storage import default_storage

missing_count = 0
for df in UserDataFile.objects.filter(processing_status='pending'):
    if df.file and not default_storage.exists(df.file.name):
        missing_count += 1

if missing_count > 0:
    send_alert(f"Warning: {missing_count} missing files detected")
```

## Troubleshooting

### Volume Not Writable

```bash
fly ssh console -a test-blue-smoke-97
touch /data/media/test.txt
# If permission denied:
# - Check volume is mounted to correct process
# - Check fly.toml has correct mount config
```

### Files Still Missing After Re-upload

Check the MEDIA_ROOT setting:

```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py shell"
>>> from django.conf import settings
>>> print(settings.MEDIA_ROOT)
'/data/media'  # Should be /data/media in production
```

### Celery Worker Can't Access Files

Ensure both app and worker processes have volume access:

```toml
# In fly.toml
[mounts]
  source = 'data'
  destination = '/data'
  processes = ['app', 'worker']  # ← Both need access
```

## Summary

✅ **Immediate Fix**: Run `check_missing_files --fix` to mark missing files as failed  
✅ **Prevention**: Code now validates files before processing  
✅ **User Action**: Users can re-upload files and they'll process correctly  
✅ **Monitoring**: Use management command to detect issues early  

## Related Documentation

- [Media Storage Fix (MEDIA_STORAGE_FIX.md)](../MEDIA_STORAGE_FIX.md) - Volume setup guide
- [Django File Storage](https://docs.djangoproject.com/en/stable/ref/files/storage/)
- [Fly.io Volumes](https://fly.io/docs/reference/volumes/)

