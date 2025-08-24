#!/usr/bin/env python3
"""
Debug NSN AMSC extraction for NSN 5310005309927
Expected result: AMSC = "B"
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_amsc_extraction():
    """Debug the AMSC extraction process step by step."""
    
    nsn = "5310005309927"
    expected_amsc = "B"
    
    print(f"🔍 Debugging AMSC extraction for NSN: {nsn}")
    print(f"🎯 Expected AMSC: {expected_amsc}")
    print("=" * 60)
    
    try:
        # Test 1: Import the scraper
        print("✓ Testing DIBBS scraper import...")
        from core.scrapers.dibbs_scraper import DibbsScraper
        print("  ✅ DIBBS scraper imported successfully")
        
        # Test 2: Initialize scraper
        print("✓ Testing scraper initialization...")
        with DibbsScraper() as scraper:
            print("  ✅ Scraper initialized successfully")
            
            # Test 3: Extract AMSC with detailed debugging
            print(f"✓ Testing AMSC extraction for NSN: {nsn}")
            print("  ⚠️  This will navigate to the DIBBS website")
            
            # Run the extraction
            amsc_result = scraper.extract_nsn_amsc(nsn)
            
            if amsc_result:
                print(f"  ✅ AMSC extraction successful!")
                print(f"  📊 Result: {amsc_result}")
                print(f"  🎯 Expected: {expected_amsc}")
                print(f"  ✅ Match: {amsc_result == expected_amsc}")
            else:
                print(f"  ❌ AMSC extraction failed - no result returned")
                
        return amsc_result == expected_amsc
        
    except Exception as e:
        print(f"\n❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_amsc_extraction_workflow():
    """Test the complete AMSC extraction workflow."""
    
    nsn = "5310005309927"
    contract_id = "test-contract-123"  # Mock contract ID for testing
    
    print(f"\n🚀 Testing complete AMSC extraction workflow")
    print("=" * 60)
    
    try:
        # Test 1: Import the workflow
        print("✓ Testing workflow import...")
        from workflows.adhoc.extract_nsn_amsc import extract_nsn_amsc
        print("  ✅ Workflow imported successfully")
        
        # Test 2: Test Supabase connection
        print("✓ Testing Supabase connection...")
        from core.uploaders.supabase_uploader import SupabaseUploader
        uploader = SupabaseUploader()
        print("  ✅ Supabase connection successful")
        
        # Test 3: Run the workflow
        print(f"✓ Running workflow for NSN: {nsn}")
        print("  ⚠️  This will extract AMSC and update database")
        
        success = extract_nsn_amsc(contract_id, nsn, verbose=True)
        
        if success:
            print(f"  ✅ Workflow completed successfully!")
        else:
            print(f"  ❌ Workflow failed!")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 NSN AMSC Extraction Debug Test")
    print("=" * 60)
    
    # Test 1: Basic extraction
    print("\n🔧 Testing basic AMSC extraction...")
    basic_success = debug_amsc_extraction()
    
    # Test 2: Complete workflow (optional)
    if basic_success:
        print(f"\n🎉 Basic extraction successful! AMSC found correctly.")
        
        response = input("\nDo you want to test the complete workflow? (y/N): ")
        if response.lower() in ['y', 'yes']:
            workflow_success = test_amsc_extraction_workflow()
            if workflow_success:
                print(f"\n🎉 Complete workflow test successful!")
            else:
                print(f"\n❌ Complete workflow test failed!")
        else:
            print(f"\n⏭️  Skipping complete workflow test")
    else:
        print(f"\n❌ Basic extraction failed - cannot test complete workflow")
        sys.exit(1)
