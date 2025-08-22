#!/usr/bin/env python3
"""
List files in Supabase storage to check naming format
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.uploaders.supabase_uploader import SupabaseUploader

def list_storage_files():
    """List all files in the docs bucket."""
    
    print("📋 Listing Storage Files...")
    print()
    
    try:
        # Initialize uploader
        uploader = SupabaseUploader()
        
        # Get storage bucket
        bucket = uploader.supabase.storage.from_('docs')
        
        # List all files
        result = bucket.list('')
        
        if result:
            print(f"Found {len(result)} files:")
            print()
            
            # Sort files by name for easier reading
            sorted_files = sorted(result, key=lambda x: x.get('name', ''))
            
            for i, file in enumerate(sorted_files, 1):
                print(f"{i:2d}. {file.get('name', 'Unknown')}")
                print(f"     Size: {file.get('metadata', {}).get('size', 'Unknown')} bytes")
                print(f"     Created: {file.get('created_at', 'Unknown')}")
                print(f"     Updated: {file.get('updated_at', 'Unknown')}")
                
                # Analyze the filename format
                filename = file.get('name', '')
                if filename.startswith('contract-'):
                    parts = filename.split('-')
                    if len(parts) >= 4:
                        prefix = parts[0]
                        contract_id = parts[1]
                        timestamp = parts[2]
                        file_part = '-'.join(parts[3:])
                        
                        print(f"     Format: {prefix}-{contract_id}-{timestamp}-{file_part}")
                        print(f"     Contract ID: {contract_id}")
                        print(f"     Timestamp: {timestamp}")
                        print(f"     Filename: {file_part}")
                    else:
                        print(f"     Format: Unexpected format (only {len(parts)} parts)")
                elif filename.startswith('rfq-'):
                    print(f"     Format: Old RFQ format")
                else:
                    print(f"     Format: Other format")
                
                print()
        else:
            print("No files found in storage.")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    list_storage_files()
