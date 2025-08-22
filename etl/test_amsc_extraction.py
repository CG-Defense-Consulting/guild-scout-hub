#!/usr/bin/env python3
"""
Test script for AMSC extraction functionality.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.uploaders.supabase_uploader import SupabaseUploader

def test_amsc_extraction():
    """Test the AMSC extraction functionality."""
    print("🧪 Testing AMSC Extraction...")
    
    try:
        # Test with a sample NSN (you can replace this with a real one)
        test_nsn = "SPE4A625T29KC"  # Replace with actual NSN from your contracts
        
        print(f"Testing with NSN: {test_nsn}")
        
        # Initialize scraper
        scraper = DibbsScraper()
        
        # Extract AMSC code
        print("Extracting AMSC code...")
        amsc_code = scraper.extract_nsn_amsc(test_nsn)
        
        if amsc_code:
            print(f"✅ AMSC code extracted: {amsc_code}")
            is_g_level = amsc_code.upper() == 'G'
            print(f"   Is G-Level: {is_g_level}")
        else:
            print("❌ Failed to extract AMSC code")
            
        # Test database update (with a dummy contract ID)
        print("\nTesting database update...")
        uploader = SupabaseUploader()
        
        # Note: This will fail if the contract ID doesn't exist
        # test_contract_id = "test-contract-id"
        # success = uploader.update_contract_amsc(test_contract_id, is_g_level)
        # print(f"Database update: {'✅ Success' if success else '❌ Failed'}")
        
        print("⚠️  Database update test skipped (requires valid contract ID)")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

if __name__ == "__main__":
    test_amsc_extraction()
