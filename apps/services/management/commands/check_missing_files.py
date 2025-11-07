"""
Management command to check for missing files in storage.

This command identifies UserDataFile records where the file reference exists in the database
but the actual file is missing from storage (local filesystem or cloud storage).
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.services.models import UserDataFile


class Command(BaseCommand):
    help = 'Check for UserDataFile records with missing files in storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check only files for a specific user ID',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Mark missing files as failed (updates status and log)',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete database records for missing files (WARNING: destructive)',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        fix = options.get('fix')
        delete = options.get('delete')

        # Query files
        queryset = UserDataFile.objects.all()
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            self.stdout.write(f"\nChecking files for user_id={user_id}...")
        else:
            self.stdout.write("\nChecking all files...")

        total_files = queryset.count()
        self.stdout.write(f"Total file records in database: {total_files}")

        # Check each file
        missing_files = []
        for data_file in queryset:
            if not data_file.file:
                missing_files.append({
                    'id': data_file.id,
                    'user_id': data_file.user_id,
                    'filename': data_file.original_filename,
                    'status': data_file.processing_status,
                    'path': None,
                    'reason': 'No file field'
                })
            elif not default_storage.exists(data_file.file.name):
                missing_files.append({
                    'id': data_file.id,
                    'user_id': data_file.user_id,
                    'filename': data_file.original_filename,
                    'status': data_file.processing_status,
                    'path': data_file.file.name,
                    'reason': 'File not in storage'
                })

        # Report findings
        if not missing_files:
            self.stdout.write(self.style.SUCCESS(f"\n✓ All {total_files} files exist in storage!"))
            return

        self.stdout.write(self.style.ERROR(f"\n✗ Found {len(missing_files)} missing files:"))
        self.stdout.write("")

        # Group by user
        by_user = {}
        for file_info in missing_files:
            uid = file_info['user_id']
            if uid not in by_user:
                by_user[uid] = []
            by_user[uid].append(file_info)

        # Display grouped results
        for uid, files in sorted(by_user.items()):
            self.stdout.write(f"\nUser {uid}: {len(files)} missing file(s)")
            for file_info in files:
                self.stdout.write(
                    f"  - ID {file_info['id']}: {file_info['filename']} "
                    f"(status={file_info['status']}, reason={file_info['reason']})"
                )
                if file_info['path']:
                    self.stdout.write(f"    Path: {file_info['path']}")

        # Apply fixes if requested
        if fix:
            self.stdout.write(self.style.WARNING("\n⚠ Marking missing files as 'failed'..."))
            fixed_count = 0
            for file_info in missing_files:
                try:
                    data_file = UserDataFile.objects.get(id=file_info['id'])
                    data_file.processing_status = 'failed'
                    data_file.processing_log = (
                        f"File missing from storage. Reason: {file_info['reason']}. "
                        f"Please re-upload your file."
                    )
                    data_file.save(update_fields=['processing_status', 'processing_log'])
                    fixed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error updating file {file_info['id']}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"✓ Updated {fixed_count} file records"))

        elif delete:
            if not self.confirm_deletion():
                self.stdout.write(self.style.WARNING("Deletion cancelled"))
                return

            self.stdout.write(self.style.WARNING("\n⚠ Deleting records for missing files..."))
            deleted_count = 0
            for file_info in missing_files:
                try:
                    UserDataFile.objects.filter(id=file_info['id']).delete()
                    deleted_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error deleting file {file_info['id']}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {deleted_count} file records"))

        else:
            self.stdout.write(self.style.WARNING(
                "\nTo mark these files as failed, run with --fix"
            ))
            self.stdout.write(self.style.WARNING(
                "To delete these records from the database, run with --delete (WARNING: destructive)"
            ))

    def confirm_deletion(self):
        """Ask user to confirm deletion."""
        self.stdout.write(self.style.WARNING(
            "\n⚠ WARNING: This will permanently delete database records!"
        ))
        response = input("Type 'yes' to confirm deletion: ")
        return response.lower() == 'yes'

