#!/usr/bin/env python3
"""
Test script to verify PDF download functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from utils.logger import setup_logger

def test_pdf_download():
    """Test PDF download with a known solicitation number."""
    logger = setup_logger(__name__)
    
    # Use a test solicitation number (you can replace with a known working one)
    test_solicitation = "SPE4A625T29KC"  # From the broken link example
    
    try:
        logger.info(f"Testing PDF download for: {test_solicitation}")
        
        # Initialize scraper
        scraper = DibbsScraper(headless=True)
        
        # Search for solicitation
        result = scraper.search_solicitation(test_solicitation)
        
        if result:
            logger.info(f"✅ Success! Downloaded PDF: {result['pdf_path']}")
            
            # Check file size
            file_size = os.path.getsize(result['pdf_path'])
            logger.info(f"📁 File size: {file_size} bytes")
            
            # Check if it's a valid PDF
            with open(result['pdf_path'], 'rb') as f:
                header = f.read(10)
                logger.info(f"🔍 File header: {header}")
                
                if header.startswith(b'%PDF'):
                    logger.info("✅ Valid PDF header detected")
                else:
                    logger.error("❌ Invalid PDF header")
            
            return True
        else:
            logger.error("❌ Failed to download PDF")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during test: {str(e)}")
        return False
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

if __name__ == "__main__":
    success = test_pdf_download()
    sys.exit(0 if success else 1)
