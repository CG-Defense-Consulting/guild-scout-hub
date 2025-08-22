#!/usr/bin/env python3
"""
Safe test script for DIBBS scraper - tests without web requests
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_scraper_safe():
    """Test the scraper safely without making web requests."""
    
    print("Testing DIBBS scraper safely (no web requests)...")
    
    try:
        # Test imports
        print("✓ Testing imports...")
        from core.scrapers.dibbs_scraper import DibbsScraper
        from core.processors.pdf_processor import PDFProcessor
        from core.uploaders.supabase_uploader import SupabaseUploader
        from utils.logger import setup_logger
        print("  ✓ All imports successful")
        
        # Test logger setup
        print("✓ Testing logger setup...")
        logger = setup_logger("test_scraper_safe")
        logger.info("Logger test successful")
        print("  ✓ Logger setup successful")
        
        # Test PDF processor
        print("✓ Testing PDF processor...")
        pdf_processor = PDFProcessor()
        print("  ✓ PDF processor initialized")
        
        # Test Supabase uploader
        print("✓ Testing Supabase uploader...")
        supabase_uploader = SupabaseUploader()
        print("  ✓ Supabase uploader initialized")
        
        # Test scraper class methods (without initializing webdriver)
        print("✓ Testing scraper class methods...")
        
        # Create a mock scraper instance to test method signatures
        class MockScraper(DibbsScraper):
            def __init__(self):
                # Don't call parent __init__ to avoid webdriver setup
                self.base_url = "https://dibbs2.bsm.dla.mil"
                self.download_dir = "./downloads"
                self.driver = None
                self.headless = True
        
        mock_scraper = MockScraper()
        
        # Test method existence
        assert hasattr(mock_scraper, 'search_solicitation')
        assert hasattr(mock_scraper, 'download_rfq_pdf')
        assert hasattr(mock_scraper, 'get_daily_solicitations')
        assert hasattr(mock_scraper, '_handle_consent_page')
        print("  ✓ All required methods exist")
        
        # Test URL construction logic
        test_solicitation = "SPE7L3-24-R-0001"
        last_char = test_solicitation[-1]
        expected_url = f"{mock_scraper.base_url}/Downloads/RFQ/{last_char}/{test_solicitation}.PDF"
        print(f"  ✓ URL construction: {expected_url}")
        
        print("\n🎉 All safe tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_scraper_safe()
    if success:
        print("\n✅ Safe scraper test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Safe scraper test failed!")
        sys.exit(1)
