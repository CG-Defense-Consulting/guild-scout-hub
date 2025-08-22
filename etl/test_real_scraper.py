#!/usr/bin/env python3
"""
Real scraper test - tests actual web scraping functionality
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_real_scraper():
    """Test the actual scraper with a real solicitation number."""
    
    print("Testing DIBBS scraper with real web requests...")
    print("⚠️  This will attempt to access the DIBBS website")
    
    try:
        # Test imports
        print("✓ Testing imports...")
        from core.scrapers.dibbs_scraper import DibbsScraper
        from utils.logger import setup_logger
        print("  ✓ All imports successful")
        
        # Set up logging
        logger = setup_logger("test_real_scraper", level=20)  # INFO level
        
        # Test solicitation number (you can change this to a real one)
        test_solicitation = "SPE7L3-24-R-0001"  # Example format
        
        print(f"✓ Testing with solicitation: {test_solicitation}")
        
        # Initialize scraper with headless=False to see what's happening
        print("✓ Initializing scraper...")
        scraper = DibbsScraper(headless=False)  # Set to False to see the browser
        print("  ✓ Scraper initialized successfully")
        
        # Test PDF download
        print("✓ Testing PDF download...")
        print("  This will open a browser and attempt to download the PDF...")
        
        result = scraper.search_solicitation(test_solicitation)
        
        if result:
            print(f"  ✓ Success! Downloaded PDF: {result.get('pdf_path')}")
            print(f"  ✓ URL: {result.get('url')}")
            
            # Test PDF processing
            print("✓ Testing PDF processing...")
            from core.processors.pdf_processor import PDFProcessor
            processor = PDFProcessor()
            extracted_data = processor.extract_rfq_data(result['pdf_path'])
            
            if extracted_data:
                print(f"  ✓ PDF processed successfully")
                print(f"  ✓ Extracted solicitation number: {extracted_data.get('solicitation_number')}")
                print(f"  ✓ Extracted title: {extracted_data.get('title', 'N/A')[:100]}...")
            else:
                print("  ⚠ PDF processing failed")
        else:
            print("  ⚠ No PDF found for this solicitation")
            print("  This could mean:")
            print("    - The solicitation number doesn't exist")
            print("    - The website structure has changed")
            print("    - There are network/access issues")
        
        # Clean up
        print("✓ Cleaning up...")
        scraper.cleanup()
        print("  ✓ Cleanup completed")
        
        print("\n🎉 Real scraper test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting real scraper test...")
    print("Make sure you have:")
    print("  - Chrome browser installed")
    print("  - Internet connection")
    print("  - Access to DIBBS website")
    print()
    
    success = test_real_scraper()
    if success:
        print("\n✅ Real scraper test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Real scraper test failed!")
        sys.exit(1)
