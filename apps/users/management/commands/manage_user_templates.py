"""
Management command to manage user-specific templates.

Usage:
    python manage.py manage_user_templates create_all
    python manage.py manage_user_templates create --user-id 1
    python manage.py manage_user_templates list
    python manage.py manage_user_templates delete --user-id 1
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from apps.users.signals import create_default_user_templates

User = get_user_model()


class Command(BaseCommand):
    help = 'Manage user-specific template folders and files'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create_all', 'create', 'list', 'delete'],
            help='Action to perform'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for create/delete actions'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create_all':
            self.create_all_user_templates()
        elif action == 'create':
            user_id = options.get('user_id')
            if not user_id:
                raise CommandError('--user-id is required for create action')
            self.create_user_templates(user_id)
        elif action == 'list':
            self.list_user_templates()
        elif action == 'delete':
            user_id = options.get('user_id')
            if not user_id:
                raise CommandError('--user-id is required for delete action')
            self.delete_user_templates(user_id)

    def create_all_user_templates(self):
        """Create template folders for all users who don't have them."""
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            user_folder = f"user_templates/user_{user.id}"
            if not default_storage.exists(user_folder):
                try:
                    # Create the user folder
                    dummy_file_path = f"{user_folder}/.gitkeep"
                    default_storage.save(dummy_file_path, content=b'')
                    
                    # Create default templates
                    create_default_user_templates(user, user_folder)
                    
                    created_count += 1
                    self.stdout.write(f"Created templates for user {user.id} ({user.email})")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to create templates for user {user.id}: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"Created templates for {created_count} users")
        )

    def create_user_templates(self, user_id):
        """Create template folder and files for a specific user."""
        try:
            user = User.objects.get(id=user_id)
            user_folder = f"user_templates/user_{user.id}"
            
            if default_storage.exists(user_folder):
                self.stdout.write(
                    self.style.WARNING(f"User {user_id} already has a template folder")
                )
                return
            
            # Create the user folder
            dummy_file_path = f"{user_folder}/.gitkeep"
            default_storage.save(dummy_file_path, content=b'')
            
            # Create default templates
            create_default_user_templates(user, user_folder)
            
            self.stdout.write(
                self.style.SUCCESS(f"Created templates for user {user_id} ({user.email})")
            )
            
        except User.DoesNotExist:
            raise CommandError(f"User with ID {user_id} does not exist")
        except Exception as e:
            raise CommandError(f"Failed to create templates for user {user_id}: {str(e)}")

    def list_user_templates(self):
        """List all users and their template folder status."""
        users = User.objects.all().order_by('id')
        
        self.stdout.write('\nUser Template Status:')
        self.stdout.write('=' * 50)
        
        for user in users:
            user_folder = f"user_templates/user_{user.id}"
            has_folder = default_storage.exists(user_folder)
            status = '✅' if has_folder else '❌'
            
            self.stdout.write(f"{status} User {user.id}: {user.email}")
            
            if has_folder:
                # List template files in the folder
                try:
                    files = default_storage.listdir(user_folder)[1]  # Get files only
                    template_files = [f for f in files if f.endswith('.html')]
                    if template_files:
                        self.stdout.write(f"    Templates: {', '.join(template_files)}")
                    else:
                        self.stdout.write("    No template files found")
                except Exception as e:
                    self.stdout.write(f"    Error listing files: {str(e)}")
        
        self.stdout.write()

    def delete_user_templates(self, user_id):
        """Delete template folder and files for a specific user."""
        try:
            user = User.objects.get(id=user_id)
            user_folder = f"user_templates/user_{user.id}"
            
            if not default_storage.exists(user_folder):
                self.stdout.write(
                    self.style.WARNING(f"User {user_id} does not have a template folder")
                )
                return
            
            # List files before deletion
            try:
                files = default_storage.listdir(user_folder)[1]
                file_count = len([f for f in files if not f.startswith('.')])
                self.stdout.write(f"Found {file_count} files in user {user_id}'s template folder")
            except:
                file_count = 0
            
            # Delete all files in the folder
            deleted_count = 0
            try:
                files = default_storage.listdir(user_folder)[1]
                for filename in files:
                    file_path = f"{user_folder}/{filename}"
                    default_storage.delete(file_path)
                    deleted_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error deleting files: {str(e)}")
                )
            
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} files for user {user_id}")
            )
            
        except User.DoesNotExist:
            raise CommandError(f"User with ID {user_id} does not exist")
        except Exception as e:
            raise CommandError(f"Failed to delete templates for user {user_id}: {str(e)}")

