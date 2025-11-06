import os
import json
import pandas as pd
import tempfile
from datetime import datetime
from pathlib import Path
import importlib.util
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from celery import shared_task
import logging

from .models import UserDataFile, UserProcessedData, Service

logger = logging.getLogger(__name__)


@shared_task
def process_user_data_file(file_id):
    """
    Process a user's uploaded data file with basic cleansing logic.
    This is a placeholder for where you would integrate user-specific GitHub repo logic.
    """
    try:
        data_file = UserDataFile.objects.get(id=file_id)
        data_file.processing_status = 'processing'
        data_file.save()
        
        logger.info(f"Starting processing for file {file_id}: {data_file.original_filename}")
        
        # Basic data processing logic (placeholder for user-specific logic)
        processed_data, summary = process_data_file(data_file)
        
        # Create processed data record
        processed_file = UserProcessedData.objects.create(
            data_file=data_file,
            processed_file=processed_data,
            summary_data=summary
        )
        
        # Update file status
        data_file.processing_status = 'completed'
        data_file.processed_at = timezone.now()
        data_file.processing_log = f"Processing completed successfully at {timezone.now()}"
        data_file.save()
        
        logger.info(f"Processing completed for file {file_id}")
        return f"File {file_id} processed successfully"
        
    except UserDataFile.DoesNotExist:
        logger.error(f"Data file {file_id} not found")
        return f"File {file_id} not found"
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}")
        
        # Update file status to failed
        try:
            data_file = UserDataFile.objects.get(id=file_id)
            data_file.processing_status = 'failed'
            data_file.processing_log = f"Processing failed: {str(e)}"
            data_file.save()
        except UserDataFile.DoesNotExist:
            pass
        
        return f"Error processing file {file_id}: {str(e)}"


def process_data_file(data_file):
    """
    Basic data processing logic. In Phase 2, this would be replaced with
    user-specific logic from their GitHub repository.
    """
    file_path = data_file.file.path
    file_type = data_file.file_type.lower()
    
    try:
        # Read the file based on type
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
        elif file_type == 'json':
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            # Convert JSON to DataFrame (assuming it's a list of records)
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            else:
                df = pd.json_normalize(json_data)
        else:
            # For txt files, try to read as CSV
            df = pd.read_csv(file_path, sep='\t')
        
        # Basic data cleansing (placeholder for user-specific logic)
        original_rows = len(df)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove duplicate rows
        df = df.drop_duplicates()
        
        # Basic string cleaning
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('', pd.NA)
        
        # Generate summary statistics
        summary = {
            'original_rows': original_rows,
            'processed_rows': len(df),
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'processing_timestamp': timezone.now().isoformat(),
            'file_type': file_type
        }
        
        # Save processed data
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{file_type}', delete=False) as tmp_file:
            if file_type == 'csv':
                df.to_csv(tmp_file.name, index=False)
            elif file_type in ['xlsx', 'xls']:
                df.to_excel(tmp_file.name, index=False)
            elif file_type == 'json':
                df.to_json(tmp_file.name, orient='records', indent=2)
            else:
                df.to_csv(tmp_file.name, index=False, sep='\t')
            
            # Read the processed file and save to storage
            with open(tmp_file.name, 'rb') as f:
                processed_content = f.read()
            
            # Clean up temp file
            os.unlink(tmp_file.name)
        
        # Create a file name for the processed data
        processed_filename = f"processed_{data_file.original_filename}"
        processed_file = ContentFile(processed_content, name=processed_filename)
        
        return processed_file, summary
        
    except Exception as e:
        logger.error(f"Error in process_data_file: {str(e)}")
        raise e


def _load_user_processed_module(user_id: int, service_name: str):
    """Dynamically load a user's processed_file.py module by absolute path.
    Falls back to None if not found.
    """
    try:
        from django.conf import settings
        # Build absolute path to user program processed_file.py (service_name directory may contain spaces)
        module_path: Path = settings.BASE_DIR / "user_programs" / f"user_{user_id}" / service_name / "processed_file.py"
        if not module_path.exists():
            logger.warning(f"processed_file.py not found at: {module_path}")
            return None
        spec = importlib.util.spec_from_file_location(f"user_{user_id}_{service_name}_processed_module", str(module_path))
        if spec is None or spec.loader is None:
            logger.warning(f"Could not create spec for module at: {module_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        return module
    except Exception as e:
        logger.error(f"Failed to load user processed module for user {user_id}, service '{service_name}': {e}")
        return None


def _call_user_batch_processor(module, data_files_queryset):
    """Attempt to call a user-defined batch function. Falls back to generic composition
    using process_customer_data + write_to_excel if available. Returns (ContentFile, summary_dict).
    """
    # Prefer any function that looks like process_user_*_files
    batch_func = None
    try:
        for attr_name in dir(module):
            if attr_name.startswith("process_user_") and attr_name.endswith("_files"):
                candidate = getattr(module, attr_name)
                if callable(candidate):
                    batch_func = candidate
                    break
    except Exception:
        batch_func = None

    if batch_func is not None:
        return batch_func(list(data_files_queryset))  # user code usually expects list/QuerySet

    # Fallback to composed approach if helpers exist
    has_helpers = all(hasattr(module, name) for name in ["process_customer_data", "write_to_excel"])
    if has_helpers:
        process_customer_data = getattr(module, "process_customer_data")
        write_to_excel = getattr(module, "write_to_excel")

        # Build list of file paths from queryset
        file_paths = [df.file.path for df in data_files_queryset]

        processed_dfs = process_customer_data(file_paths)

        # Write to temp excel
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as tmp_file:
            output_path = tmp_file.name

        final_path = write_to_excel(processed_dfs, output_path)

        # Read file content and wrap as ContentFile
        with open(final_path, 'rb') as f:
            content = f.read()

        # Best-effort cleanup
        try:
            os.unlink(final_path)
        except Exception:
            pass

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"processed_batch_{timestamp}.xlsx"
        processed_file_cf = ContentFile(content, name=filename)

        # Minimal summary
        summary = {
            "files_processed": int(len(file_paths)),
            "processing_timestamp": timezone.now().isoformat(),
        }
        return processed_file_cf, summary

    raise RuntimeError("No suitable batch processor found in user module")


@shared_task
def process_all_user_files(user_id: int, service_slug: str):
    """Process all files for a user+service in a single batch using the user's processed_file.py."""
    try:
        service = Service.objects.get(slug=service_slug)
        # Get ALL files for this user+service, regardless of status
        all_files = UserDataFile.objects.filter(user_id=user_id, service=service).order_by('-created_at')

        if not all_files.exists():
            logger.info(f"No files to process for user={user_id}, service={service_slug}")
            return "No files to process"

        # Load user-specific module by service name (directory name matches Service.name)
        module = _load_user_processed_module(user_id=user_id, service_name=service.name)
        if module is None:
            raise RuntimeError("User processed module not found")

        # Mark files as processing
        all_files.update(processing_status='processing')

        processed_file_cf, summary = _call_user_batch_processor(module, all_files)

        # Anchor the processed output to the most recent file so it shows in the UI
        anchor_file = all_files.first()
        UserProcessedData.objects.create(
            data_file=anchor_file,
            processed_file=processed_file_cf,
            summary_data=summary or {},
        )

        # Mark all included files as completed with a log reference
        now_ts = timezone.now()
        for df in all_files:
            df.processing_status = 'completed'
            df.processed_at = now_ts
            df.processing_log = f"Included in batch output on {now_ts} (anchored to file ID {anchor_file.id})"
            df.save(update_fields=["processing_status", "processed_at", "processing_log"])

        logger.info(f"Batch processed {all_files.count()} files for user={user_id}, service={service_slug}")
        return f"Batch processed {all_files.count()} file(s)"

    except Exception as e:
        logger.error(f"Error in batch processing for user={user_id}, service={service_slug}: {e}")
        # Attempt to mark files as failed
        try:
            service = Service.objects.get(slug=service_slug)
            pending_files = UserDataFile.objects.filter(user_id=user_id, service=service, processing_status__in=['pending','processing'])
            for df in pending_files:
                df.processing_status = 'failed'
                df.processing_log = f"Batch processing failed: {e}"
                df.save(update_fields=["processing_status", "processing_log"])
        except Exception:
            pass
        return f"Error: {e}"


@shared_task
def cleanup_old_files():
    """
    Cleanup task to remove old processed files and temporary data.
    Run this periodically to manage storage.
    """
    from datetime import timedelta
    
    # Delete files older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    old_files = UserDataFile.objects.filter(
        created_at__lt=cutoff_date,
        processing_status='completed'
    )
    
    deleted_count = 0
    for data_file in old_files:
        try:
            # Delete the file from storage
            if data_file.file:
                data_file.file.delete(save=False)
            
            # Delete processed data if it exists
            if hasattr(data_file, 'processed_data'):
                if data_file.processed_data.processed_file:
                    data_file.processed_data.processed_file.delete(save=False)
                data_file.processed_data.delete()
            
            # Delete the data file record
            data_file.delete()
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Error deleting file {data_file.id}: {str(e)}")
    
    logger.info(f"Cleanup completed: {deleted_count} old files deleted")
    return f"Cleaned up {deleted_count} old files"
