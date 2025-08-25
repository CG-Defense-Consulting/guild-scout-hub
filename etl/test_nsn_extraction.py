#!/usr/bin/env python3
"""
Test script for NSN extraction operation
"""

import os
import sys
import logging
from pathlib import Path

# Add the etl directory to the Python path
etl_dir = Path(__file__).parent
sys.path.insert(0, str(etl_dir))

from core.operations import ChromeSetupOperation, NsnExtractionOperation
from utils.logger import setup_logger

def test_nsn_extraction():
    """Test NSN extraction for a single NSN."""
    
    # Setup logging
    logger = setup_logger("test_nsn_extraction")
    logger.info("🧪 Starting NSN extraction test")
    
    # Test NSN
    test_nsn = "8455016887455"
    logger.info(f"🧪 Testing NSN: {test_nsn}")
    
    try:
        # Set up Chrome
        logger.info("🧪 Setting up Chrome...")
        chrome_setup = ChromeSetupOperation(headless=True)
        
        # Create empty context that will be populated by ChromeSetupOperation
        context = {}
        chrome_result = chrome_setup.execute({}, context)
        
        if not chrome_result.success:
            logger.error(f"❌ Chrome setup failed: {chrome_result.error}")
            return False
        
        logger.info("✅ Chrome setup successful")
        
        # Get the driver from the context (not from the result data)
        driver = context.get('chrome_driver')
        download_dir = context.get('chrome_download_dir')
        
        if not driver:
            logger.error("❌ No driver returned from Chrome setup")
            logger.error(f"Context keys: {list(context.keys())}")
            return False
        
        # Step 2: Handle consent page
        logger.info("🧪 Handling consent page...")
        from core.operations import ConsentPageOperation
        consent_operation = ConsentPageOperation()
        consent_result = consent_operation.execute({'nsn': test_nsn}, context)
        
        if not consent_result.success:
            logger.error(f"❌ Consent page handling failed: {consent_result.error}")
            return False
        
        logger.info("✅ Consent page handled successfully")
        
        # Debug: Check what page we're on after consent
        driver = context.get('chrome_driver')
        logger.info(f"🧪 Current URL after consent: {driver.current_url}")
        logger.info(f"🧪 Page title after consent: {driver.title}")
        
        # Debug: Look for any text containing "AMSC" on the page
        page_source = driver.page_source
        logger.info(f"🧪 Page source length: {len(page_source)}")
        
        # Look for AMSC-related text
        if "AMSC" in page_source.upper():
            logger.info("🧪 Found 'AMSC' text in page source")
            # Find the line containing AMSC
            lines = page_source.split('\n')
            for i, line in enumerate(lines):
                if 'AMSC' in line.upper():
                    logger.info(f"🧪 Line {i+1} with AMSC: {line.strip()}")
        else:
            logger.info("🧪 No 'AMSC' text found in page source")
        
        # Step 3: Extract AMSC code
        logger.info("🧪 Starting AMSC code extraction...")
        nsn_extraction = NsnExtractionOperation()
        
        # Execute NSN extraction
        extraction_result = nsn_extraction.execute(
            inputs={'nsn': test_nsn, 'check_closed_status': True},
            context=context
        )
        
        if extraction_result.success:
            logger.info("✅ NSN extraction successful")
            logger.info(f"🧪 Extracted data: {extraction_result.data}")
            logger.info(f"🧪 Metadata: {extraction_result.metadata}")
        else:
            logger.error(f"❌ NSN extraction failed: {extraction_result.error}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        return False
    
    finally:
        # Clean up
        if 'driver' in locals():
            try:
                driver.quit()
                logger.info("🧪 Chrome driver closed")
            except:
                pass

if __name__ == "__main__":
    success = test_nsn_extraction()
    if success:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")
        sys.exit(1)
