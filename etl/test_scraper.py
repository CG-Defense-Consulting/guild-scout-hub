#!/usr/bin/env python3
"""
Test script for DIBBS scraper
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from utils.logger import setup_logger

def test_scraper():
    """Test the DIBBS scraper functionality."""
    
    # Set up logging
    logger = setup_logger("test_scraper", level=20)  # INFO level
    
    # Test solicitation number (you'll need to provide a real one)
    test_solicitation = "SPE7L3-24-R-0001"  # Example format
    
    logger.info(f"Testing DIBBS scraper with solicitation: {test_solicitation}")
    
    try:
        # Initialize scraper
        scraper = DibbsScraper(headless=False)  # Set to False to see what's happening
        
        # Test PDF download
        logger.info("Testing PDF download...")
        result = scraper.search_solicitation(test_solicitation)
        
        if result:
            logger.info(f"Success! Downloaded PDF: {result.get('pdf_path')}")
            logger.info(f"URL: {result.get('url')}")
        else:
            logger.warning("No PDF found for this solicitation")
        
        # Clean up
        scraper.cleanup()
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")
        sys.exit(1)
