#!/usr/bin/env python3
"""
Script to upload environment variables from a .env file to Fly.io app
Usage: python upload_env_vars.py <env_file>
"""

import os
import sys
import subprocess
import re
from pathlib import Path


def parse_env_file(file_path):
    """Parse .env file and return a dictionary of key-value pairs."""
    env_vars = {}
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Split on first '=' to handle values with '=' in them
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Skip empty values or placeholder values
                if value and not value.endswith('***') and value != '""' and value != "''":
                    env_vars[key] = value
                elif value.endswith('***'):
                    print(f"⚠️  Skipping placeholder value for {key}: {value}")
                elif not value or value in ['""', "''"]:
                    print(f"⚠️  Skipping empty value for {key}")
            else:
                print(f"⚠️  Skipping malformed line {line_num}: {line}")
    
    return env_vars


def upload_to_fly(env_vars, app_name=None):
    """Upload environment variables to Fly app using fly secrets set."""
    if not env_vars:
        print("❌ No environment variables to upload")
        return False
    
    # Build the fly secrets set command
    cmd = ['fly', 'secrets', 'set']
    
    if app_name:
        cmd.extend(['--app', app_name])
    
    # Add all environment variables as key=value pairs
    for key, value in env_vars.items():
        cmd.append(f"{key}={value}")
    
    print(f"🚀 Uploading {len(env_vars)} environment variables to Fly app...")
    print(f"Command: {' '.join(cmd[:3])} [variables...]")
    
    try:
        # Run the command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Environment variables uploaded successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to upload environment variables:")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ 'fly' command not found. Make sure Fly CLI is installed and in your PATH")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python upload_env_vars.py <env_file>")
        print("Example: python upload_env_vars.py prod.env")
        sys.exit(1)
    
    env_file = sys.argv[1]
    
    # Check if file exists
    if not Path(env_file).exists():
        print(f"❌ File not found: {env_file}")
        sys.exit(1)
    
    print(f"📖 Reading environment variables from {env_file}...")
    
    # Parse the environment file
    env_vars = parse_env_file(env_file)
    
    if not env_vars:
        print("❌ No valid environment variables found in the file")
        sys.exit(1)
    
    print(f"📋 Found {len(env_vars)} environment variables:")
    for key in sorted(env_vars.keys()):
        print(f"  - {key}")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to upload these variables to your Fly app? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Upload cancelled")
        sys.exit(0)
    
    # Upload to Fly
    success = upload_to_fly(env_vars)
    
    if success:
        print("\n🎉 Done! You can verify the secrets with: fly secrets list")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

