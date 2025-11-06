from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Deletes a user by username or email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', 
            type=str, 
            help='Specify the username of the user to delete'
        )
        parser.add_argument(
            '--email', 
            type=str, 
            help='Specify the email of the user to delete'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')

        if not username and not email:
            raise CommandError('You must provide either --username or --email')

        try:
            # Fetch the user based on the provided identifier
            if username:
                user = User.objects.get(username=username)
            elif email:
                user = User.objects.get(email=email)

            # Prompt for confirmation
            confirm = input(f"Are you sure you want to delete the user '{user}'? Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion canceled.'))
                return

            # Delete the user
            user.delete()
            self.stdout.write(self.style.SUCCESS(f"User '{user}' deleted successfully."))

        except User.DoesNotExist:
            raise CommandError("User not found")
