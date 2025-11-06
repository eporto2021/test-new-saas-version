#!/usr/bin/env python3
"""
Django SECRET_KEY generator script
Generates a cryptographically secure secret key for Django applications.
"""

import secrets
import string
import sys


def generate_secret_key(length=50):
    """
    Generate a Django SECRET_KEY using cryptographically secure random generation.
    
    Args:
        length (int): Length of the secret key (default: 50)
    
    Returns:
        str: A secure secret key suitable for Django
    """
    # Django secret keys typically use these characters
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    
    # Generate a secure random string
    secret_key = ''.join(secrets.choice(chars) for _ in range(length))
    
    return secret_key


def main():
    """Main function to generate and display secret keys."""
    print("🔐 Django SECRET_KEY Generator")
    print("=" * 40)
    
    # Generate a standard 50-character key
    standard_key = generate_secret_key(50)
    print(f"Standard (50 chars): {standard_key}")
    print()
    
    # Generate a longer key for extra security
    long_key = generate_secret_key(64)
    print(f"Long (64 chars):     {long_key}")
    print()
    
    # Generate multiple keys for comparison
    print("Multiple keys (for comparison):")
    for i in range(3):
        key = generate_secret_key(50)
        print(f"  {i+1}. {key}")
    
    print()
    print("💡 Usage:")
    print("  - Copy one of the keys above")
    print("  - Add it to your .env file: SECRET_KEY=\"your_key_here\"")
    print("  - Or set it as an environment variable")
    print("  - Never commit secret keys to version control!")
    
    # If run with --copy flag, copy the first key to clipboard (if possible)
    if len(sys.argv) > 1 and sys.argv[1] == "--copy":
        try:
            import pyperclip
            pyperclip.copy(standard_key)
            print(f"\n✅ Copied to clipboard: {standard_key}")
        except ImportError:
            print("\n⚠️  pyperclip not installed. Install with: pip install pyperclip")
        except Exception as e:
            print(f"\n⚠️  Could not copy to clipboard: {e}")


if __name__ == "__main__":
    main()

