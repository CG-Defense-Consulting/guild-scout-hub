#!/usr/bin/env python3
"""
Test Supabase connection and available keys
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.uploaders.supabase_uploader import SupabaseUploader

def test_connection():
    """Test Supabase connection with available keys."""
    
    print("🔍 Testing Supabase Connection...")
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    # Check environment variables
    print("📋 Environment Variables:")
    print(f"VITE_SUPABASE_URL: {'✓ Set' if os.getenv('VITE_SUPABASE_URL') else '✗ Missing'}")
    print(f"VITE_SUPABASE_PUBLISHABLE_KEY: {'✓ Set' if os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY') else '✗ Missing'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✓ Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '✗ Missing'}")
    print()
    
    # Try to initialize the uploader
    try:
        print("🚀 Initializing Supabase Uploader...")
        uploader = SupabaseUploader()
        print("✅ Supabase client initialized successfully!")
        
        # Test storage access
        print("📦 Testing storage access...")
        bucket = uploader.supabase.storage.from_('docs')
        print("✅ Storage bucket access successful!")
        
        # Try to list files (this should work even with anonymous access)
        print("📋 Testing file listing...")
        result = bucket.list('')
        print(f"✅ File listing successful! Found {len(result) if result else 0} files")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
