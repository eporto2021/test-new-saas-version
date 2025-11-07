# Fix: Multiple Machines with Different Volumes

## Problem Discovered

The app is running on **multiple machines with separate volumes**:
- App machine: `vol_vdmk7mnx2onp17xv`
- Worker machine: `vol_vdmk7ezom9x69gxv`

When user uploads a file → goes to app volume
When worker processes file → looks in worker volume (different!)
Result: "File not found" error

## Solution: Single Machine Architecture

Run all processes (app, worker, beat) on ONE machine sharing ONE volume.

## Steps to Fix

### 1. Deploy Updated Configuration

```bash
fly deploy -a test-blue-smoke-97
```

This will deploy the updated `fly.toml` which now has:
```toml
[[vm]]
  processes = ['worker', 'app', 'beat']  # All on one machine
```

### 2. Stop Extra Machines

After deploy, you'll still have old machines running. Stop them:

```bash
# List machines to see which ones to stop
fly machines list -a test-blue-smoke-97

# Stop the standalone beat machine
fly machine stop 48ed099f11e628 -a test-blue-smoke-97

# Stop old worker machine (if still running)
fly machine stop 2871570b5d4408 -a test-blue-smoke-97
```

### 3. Verify Single Machine Setup

```bash
fly machines list -a test-blue-smoke-97
```

You should see only ONE machine running with:
- PROCESS GROUP: app (but running all three processes)
- VOLUME: attached
- STATE: started

### 4. Test File Upload

1. Have user 9 upload files again
2. Files should process successfully now
3. All processes share the same volume

## Alternative: Object Storage (Future)

If you need multiple machines for scaling, use S3-compatible object storage:

1. Set up AWS S3 or Backblaze B2
2. Install `django-storages`:
```bash
pip install django-storages[boto3]
```

3. Update settings:
```python
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_REGION_NAME = 'us-east-1'
# etc.
```

But for now, single machine is simpler and works fine for your scale.

## Why This Happened

Fly.io volumes can only attach to ONE machine at a time. When you have separate machines for app and worker, each needs its own volume. But for file sharing, they need the same volume!

## Verification Commands

After fixing:

```bash
# Check only one machine is running
fly machines list -a test-blue-smoke-97

# SSH and verify volume
fly ssh console -a test-blue-smoke-97 -C "df -h | grep data"

# Check processes running on that machine
fly ssh console -a test-blue-smoke-97 -C "ps aux | grep -E 'gunicorn|celery'"
```

You should see:
- One machine
- One volume mounted at `/data`
- Both gunicorn AND celery processes running

## Files to Deploy

- ✅ `fly.toml` - Updated to run all processes on one machine
- ✅ `apps/services/tasks.py` - Better error handling (already deployed)
- ✅ `apps/services/management/commands/check_missing_files.py` - Diagnostic tool

---

**Deploy now**: `fly deploy -a test-blue-smoke-97`

