# File Processing Error - Fixed

## What Happened

User 9 tried to process files but got this error:
```
[Errno 2] No such file or directory: '/data/media/user_data/user_9/2025/11/07/RUN_SHEET_Sunday_2nd_November_Formatted.xlsx'
```

**Root Cause**: File records exist in the database but actual files are missing from the `/data/media` volume in production.

This likely happened because files were uploaded before the volume was properly configured/mounted.

## What I Fixed

### 1. Made Code More Robust (`apps/services/tasks.py`)

✅ **Added file existence checks** - Now validates files exist before processing  
✅ **Storage backend compatibility** - Uses `default_storage.exists()` and `.open()` instead of `.path`  
✅ **Better error messages** - Clear messages about which files are missing  
✅ **Proper temp file handling** - Works with any storage backend, not just local filesystem  
✅ **Graceful error handling** - Marks files as failed with user-friendly messages  

### 2. Created Diagnostic Tool

New management command: `check_missing_files.py`

This helps you:
- Find all missing files in the database
- See which users are affected
- Mark missing files as "failed" so users can re-upload
- Delete orphaned database records (optional)

## Immediate Action Required

### Step 1: Check for Missing Files

SSH into production and run the diagnostic:

```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files"
```

This will show you exactly which files are missing.

### Step 2: Fix the Records

Mark missing files as failed (recommended):

```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --fix"
```

This will:
- Update status to 'failed'
- Add message: "File missing from storage. Please re-upload your file."
- Users will see this and can re-upload

### Step 3: Deploy the Fix

The code changes are ready. Deploy them:

```bash
fly deploy -a test-blue-smoke-97
```

### Step 4: Test

After deployment:
1. User 9 should see their file marked as "failed"
2. They can re-upload the file
3. Processing should work correctly now

## For User 9 Specifically

Check their files:
```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --user-id 9"
```

Then fix them:
```bash
fly ssh console -a test-blue-smoke-97 -C "python manage.py check_missing_files --user-id 9 --fix"
```

## Testing in Development

Before deploying, you can test locally:

```bash
# Check for any issues
python manage.py check_missing_files

# Test with a specific user
python manage.py check_missing_files --user-id 1
```

## What Changed

### Files Modified:
1. ✅ `apps/services/tasks.py` - Better error handling and file validation
2. ✅ `apps/services/management/commands/check_missing_files.py` - New diagnostic tool

### Files Created:
1. ✅ `docs/FILE_STORAGE_FIX.md` - Comprehensive guide
2. ✅ `FILE_PROCESSING_ERROR_FIX.md` - This quick reference (can delete after reading)

## Prevention Going Forward

The updated code will now:
- Check files exist before processing
- Give clear error messages
- Handle storage backends properly
- Not crash on missing files

## If You See This Error Again

1. Run: `python manage.py check_missing_files --fix`
2. Notify the affected user(s) to re-upload
3. Investigate why files went missing (volume issue, cleanup script, etc.)

## Documentation

For detailed information, see:
- `docs/FILE_STORAGE_FIX.md` - Complete guide with troubleshooting
- `MEDIA_STORAGE_FIX.md` - Volume setup guide (already exists)

## Next Steps

1. ✅ Review the changes (already done in this file)
2. ⏭️ Run `check_missing_files` in production
3. ⏭️ Run `check_missing_files --fix` to mark files as failed
4. ⏭️ Deploy the code changes
5. ⏭️ Notify User 9 to re-upload their file

---

**Status**: Ready to deploy  
**Priority**: High (user is blocked)  
**Impact**: Fixes current error + prevents future occurrences

