# Media Storage Fix for Production

## Problem

Users couldn't upload files in production because:
- `/code/media` directory is read-only
- No persistent storage configured
- Error: `PermissionError: [Errno 13] Permission denied: '/code/media'`

## Solution

Set up a Fly.io volume for persistent media file storage.

## Implementation Steps

### 1. Create the Volume (Run this command)

```bash
fly volumes create data --size 10 --region syd -a test-blue-smoke-97
```

This creates a 10GB volume in Sydney region. You can adjust size as needed.

### 2. Deploy the Changes

The following files have been updated:
- ✅ `fly.toml` - Added volume mount configuration
- ✅ `test/settings_production.py` - Updated MEDIA_ROOT to use `/data/media`

Now deploy:

```bash
fly deploy -a test-blue-smoke-97
```

### 3. Verify

After deployment:

```bash
# Check the volume is mounted
fly ssh console -C "ls -la /data" -a test-blue-smoke-97

# Expected output: media/ directory should exist
```

Then try uploading a file as user_9 in production - it should work!

## What Changed

### fly.toml
Added volume mount:
```toml
[mounts]
  source = 'data'
  destination = '/data'
  processes = ['app', 'worker']
```

### settings_production.py
Changed MEDIA_ROOT:
```python
# Old: MEDIA_ROOT = BASE_DIR / "media"  # /code/media (read-only)
# New: MEDIA_ROOT = Path('/data/media')  # /data/media (persistent volume)
```

## Benefits

✅ **Persistent Storage**: Files survive deployments and restarts  
✅ **Writable**: No more permission errors  
✅ **Automatic**: Media directory is created automatically  
✅ **Shared**: Both app and worker processes can access files  

## Volume Management

### Check volume status
```bash
fly volumes list -a test-blue-smoke-97
```

### Increase volume size (if needed)
```bash
fly volumes extend <volume_id> --size 20 -a test-blue-smoke-97
```

### Backup considerations
Fly.io volumes are backed up automatically, but for critical data consider:
- Regular exports to S3/cloud storage
- Application-level backups

## Cost

Fly.io volumes cost approximately:
- **$0.15/GB per month**
- 10GB volume = ~$1.50/month

## Troubleshooting

### Volume not mounted
```bash
fly ssh console -C "df -h | grep data" -a test-blue-smoke-97
```

### Permission issues
The volume should be writable by the app user. If issues persist:
```bash
fly ssh console -C "ls -la /data" -a test-blue-smoke-97
```

### Files not persisting
Ensure the volume is mounted to the correct processes in fly.toml (app and worker).

---

**Status**: Ready to deploy  
**Next Step**: Run `fly volumes create data --size 10 --region syd -a test-blue-smoke-97`  
**Then**: `fly deploy -a test-blue-smoke-97`

