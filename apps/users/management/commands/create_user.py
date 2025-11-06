from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model, login
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import webbrowser
import os
import subprocess
import tempfile
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a new user with default arguments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username', 
            type=str, 
            help='Username for the new user'
        )
        parser.add_argument(
            '--email', 
            type=str, 
            help='Email address for the new user'
        )
        parser.add_argument(
            '--password', 
            type=str, 
            help='Password for the new user'
        )
        parser.add_argument(
            '--first-name', 
            type=str, 
            help='First name for the new user'
        )
        parser.add_argument(
            '--last-name', 
            type=str, 
            help='Last name for the new user'
        )
        parser.add_argument(
            '--superuser', 
            action='store_true', 
            help='Make the user a superuser'
        )
        parser.add_argument(
            '--staff', 
            action='store_true', 
            help='Make the user a staff member'
        )
        parser.add_argument(
            '--no-input', 
            action='store_true', 
            help='Use default values without prompting for input'
        )
        parser.add_argument(
            '--auto-login', 
            action='store_true', 
            help='Automatically log in the user after creation (creates a session)'
        )
        parser.add_argument(
            '--open-browser', 
            action='store_true', 
            help='Open browser to localhost:8000 with the user logged in'
        )

    def handle(self, *args, **options):
        no_input = options.get('no_input', False)
        
        # Get values from arguments or use defaults
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        is_superuser = options.get('superuser', False)
        is_staff = options.get('staff', False)
        
        # If no_input is False, prompt for missing values
        if not no_input:
            if not username:
                username = input('Username: ')
            if not email:
                email = input('Email: ')
            if not password:
                password = input('Password: ')
                if not password:
                    password = 'defaultpassword123'  # Default password
                    self.stdout.write(self.style.WARNING('Using default password: defaultpassword123'))
        
        # Use defaults if still missing
        if not username:
            username = 'user' + str(User.objects.count() + 1)  # Default username
        if not email:
            email = f'{username}@example.com'  # Default email
        if not password:
            password = 'defaultpassword123'  # Default password
        if not first_name:
            first_name = 'Default'  # Default first name
        if not last_name:
            last_name = 'User'  # Default last name
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User with username "{username}" already exists')
        
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists')
        
        try:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_superuser=is_superuser,
                is_staff=is_staff
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created user "{user}"')
            )
            
            # Show user details
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Full Name: {user.get_full_name()}')
            self.stdout.write(f'  Superuser: {user.is_superuser}')
            self.stdout.write(f'  Staff: {user.is_staff}')
            
            # Show password when --no-input is used (for automation)
            if no_input:
                self.stdout.write(f'  Password: {password}')
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=== LOGIN CREDENTIALS ==='))
                self.stdout.write(f'Username/Email: {user.email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write('')
            
            # Auto-login if requested
            session_key = None
            if options.get('auto_login', False) or options.get('open_browser', False):
                try:
                    # Create a mock request object for login
                    from django.test import RequestFactory
                    from django.contrib.sessions.backends.db import SessionStore
                    
                    # Create a new session
                    session = SessionStore()
                    session.create()
                    session_key = session.session_key
                    
                    # Save user ID in session
                    session['_auth_user_id'] = str(user.pk)
                    session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
                    session.save()
                    
                    # Create a session object in the database
                    Session.objects.create(
                        session_key=session.session_key,
                        session_data=session.encode(session._session),
                        expire_date=timezone.now() + timedelta(days=30)  # 30 day session
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'User automatically logged in!')
                    )
                    self.stdout.write(f'  Session Key: {session.session_key}')
                    self.stdout.write(f'  Session expires in 30 days')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'User created but auto-login failed: {str(e)}')
                    )
                    session_key = None
            
            # Open browser if requested
            if options.get('open_browser', False):
                try:
                    url = 'http://localhost:8000'
                    self.stdout.write(f'Opening Chrome browser to {url}...')
                    
                    # Create a simpler bookmarklet for auto-fill
                    # Create bookmarklet with proper escaping
                    auto_fill_script = "javascript:(function(){" + \
                        "var e=document.querySelector('input[name=\"email\"],input[name=\"username\"],input[name=\"login\"],input[type=\"email\"],input[id*=\"email\"],input[id*=\"username\"]');" + \
                        "var p=document.querySelector('input[name=\"password\"],input[type=\"password\"],input[id*=\"password\"]');" + \
                        f"if(e&&p){{e.value='{user.email}';p.value='{password}';e.dispatchEvent(new Event('input',{{bubbles:true}}));p.dispatchEvent(new Event('input',{{bubbles:true}}));alert('Form filled! Email: {user.email}');}}else{{alert('Form not found. Email: {user.email}\\nPassword: {password}');}}}})();"
                    
                    # Try to open Chrome with specific commands
                    chrome_commands = [
                        # macOS Chrome
                        ['open', '-a', 'Google Chrome', url],
                        # Linux Chrome
                        ['google-chrome', '--new-tab', url],
                        ['chromium-browser', '--new-tab', url],
                        ['chrome', '--new-tab', url],
                        # Windows Chrome (if running on Windows)
                        ['start', 'chrome', url],
                    ]
                    
                    chrome_opened = False
                    for cmd in chrome_commands:
                        try:
                            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            chrome_opened = True
                            break
                        except (FileNotFoundError, subprocess.SubprocessError):
                            continue
                    
                    if not chrome_opened:
                        # Fallback to default browser
                        webbrowser.open(url)
                    
                    self.stdout.write(
                        self.style.SUCCESS('Chrome browser opened to localhost:8000')
                    )
                    
                    # Display credentials and instructions
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=== LOGIN INSTRUCTIONS ==='))
                    self.stdout.write(f'Username/Email: {user.email}')
                    self.stdout.write(f'Password: {password}')
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=== METHOD 1: Auto-Fill Bookmarklet ==='))
                    self.stdout.write('1. Navigate to the login page in Chrome')
                    self.stdout.write('2. Copy this entire line and paste it in the address bar:')
                    self.stdout.write('')
                    self.stdout.write(self.style.WARNING(auto_fill_script))
                    self.stdout.write('')
                    self.stdout.write('3. Press Enter')
                    self.stdout.write('4. The form should auto-fill')
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=== METHOD 2: Manual Entry (if bookmarklet fails) ==='))
                    self.stdout.write('1. Go to the login page')
                    self.stdout.write(f'2. Enter Email: {user.email}')
                    self.stdout.write(f'3. Enter Password: {password}')
                    self.stdout.write('4. Click Login')
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=== METHOD 3: Direct Login URL (if available) ==='))
                    self.stdout.write('Try navigating directly to: http://localhost:8000/accounts/login/')
                    self.stdout.write('or: http://localhost:8000/login/')
                    
                    if session_key:
                        self.stdout.write('')
                        self.stdout.write(self.style.SUCCESS('User session is active! You should be logged in automatically.'))
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to open Chrome: {str(e)}')
                    )
                    # Fallback to regular browser
                    try:
                        webbrowser.open('http://localhost:8000')
                        self.stdout.write('Opened default browser instead.')
                    except:
                        pass
                    self.stdout.write(f'  Please manually navigate to http://localhost:8000')
                    self.stdout.write(f'  Username: {user.email}')
                    self.stdout.write(f'  Password: {password}')
            
        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')
