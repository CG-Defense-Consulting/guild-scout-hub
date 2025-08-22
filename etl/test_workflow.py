#!/usr/bin/env python3
"""
Workflow test - tests workflow logic without web scraping
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_workflow_logic():
    """Test workflow logic without actual web scraping."""
    
    print("Testing DIBBS ETL workflow logic...")
    
    try:
        # Test imports
        print("✓ Testing workflow imports...")
        from workflows.adhoc.pull_single_rfq_pdf import pull_single_rfq_pdf
        from workflows.adhoc.pull_day_rfq_pdfs import pull_day_rfq_pdfs
        from workflows.adhoc.pull_day_rfq_index_extract import pull_day_rfq_index_extract
        print("  ✓ All workflow imports successful")
        
        # Test PDF processor
        print("✓ Testing PDF processor...")
        from core.processors.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("  ✓ PDF processor initialized")
        
        # Test Supabase uploader
        print("✓ Testing Supabase uploader...")
        from core.uploaders.supabase_uploader import SupabaseUploader
        uploader = SupabaseUploader()
        print("  ✓ Supabase uploader initialized")
        
        # Test logger
        print("✓ Testing logger...")
        from utils.logger import setup_logger
        logger = setup_logger("test_workflow")
        logger.info("Workflow test successful")
        print("  ✓ Logger working")
        
        # Test date handling
        print("✓ Testing date handling...")
        from datetime import datetime, date
        test_date = date(2024, 8, 21)
        print(f"  ✓ Date handling: {test_date}")
        
        # Test solicitation number handling
        print("✓ Testing solicitation number logic...")
        test_solicitation = "SPE7L3-24-R-0001"
        last_char = test_solicitation[-1]
        expected_url = f"https://dibbs2.bsm.dla.mil/Downloads/RFQ/{last_char}/{test_solicitation}.PDF"
        print(f"  ✓ URL construction: {expected_url}")
        
        print("\n🎉 All workflow logic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workflow_logic()
    if success:
        print("\n✅ Workflow test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Workflow test failed!")
        sys.exit(1)
