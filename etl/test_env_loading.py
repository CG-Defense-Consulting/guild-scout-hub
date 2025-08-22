#!/usr/bin/env python3
"""
Test environment variable loading
"""

import os
from pathlib import Path
import dotenv

print("🔍 Testing Environment Variable Loading...")
print()

# Check current environment
print("📋 Current Environment Variables:")
print(f"VITE_SUPABASE_URL: {'✓ Set' if os.getenv('VITE_SUPABASE_URL') else '✗ Missing'}")
print(f"VITE_SUPABASE_PUBLISHABLE_KEY: {'✓ Set' if os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY') else '✗ Missing'}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {'✓ Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '✗ Missing'}")
print()

# Try to load .env file
print("📁 Looking for .env file...")
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
env_file = project_root / '.env'

print(f"Current file: {current_file}")
print(f"Project root: {project_root}")
print(f"Env file path: {env_file}")
print(f"Env file exists: {env_file.exists()}")
print()

if env_file.exists():
    print("📖 Loading .env file...")
    dotenv.load_dotenv(env_file)
    print("✅ .env file loaded")
    
    print("\n📋 Environment Variables After Loading:")
    print(f"VITE_SUPABASE_URL: {'✓ Set' if os.getenv('VITE_SUPABASE_URL') else '✗ Missing'}")
    print(f"VITE_SUPABASE_PUBLISHABLE_KEY: {'✓ Set' if os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY') else '✗ Missing'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✓ Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '✗ Missing'}")
    
    # Show first few characters of keys for verification
    url = os.getenv('VITE_SUPABASE_URL')
    pub_key = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if url:
        print(f"URL preview: {url[:50]}...")
    if pub_key:
        print(f"Publishable key preview: {pub_key[:50]}...")
    if service_key:
        print(f"Service role key preview: {service_key[:50]}...")
else:
    print("❌ .env file not found!")
