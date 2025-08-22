#!/usr/bin/env python3
"""
Simple test script for DIBBS scraper - basic functionality test
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_basic_functionality():
    """Test basic functionality without actual web scraping."""
    
    print("Testing DIBBS ETL module basic functionality...")
    
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
        logger = setup_logger("test_logger")
        logger.info("Logger test successful")
        print("  ✓ Logger setup successful")
        
        # Test PDF processor initialization
        print("✓ Testing PDF processor...")
        pdf_processor = PDFProcessor()
        print("  ✓ PDF processor initialized")
        
        # Test Supabase uploader initialization
        print("✓ Testing Supabase uploader...")
        try:
            supabase_uploader = SupabaseUploader()
            print("  ✓ Supabase uploader initialized")
        except Exception as e:
            print(f"  ⚠ Supabase uploader failed (expected if no .env): {str(e)}")
        
        # Test scraper initialization (without webdriver)
        print("✓ Testing scraper class structure...")
        # We'll test the class without initializing the webdriver
        scraper_class = DibbsScraper
        print("  ✓ Scraper class accessible")
        
        print("\n🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n✅ Basic functionality test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Basic functionality test failed!")
        sys.exit(1)
