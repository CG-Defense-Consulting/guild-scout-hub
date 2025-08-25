#!/usr/bin/env python3
"""
Extract NSN AMSC Code Workflow

This workflow accesses the NSN Details page for a contract, extracts the AMSC code,
and updates the rfq_index_extract table with the cde_g text field containing the actual AMSC code.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def extract_nsn_amsc(contract_id: str, nsn: str) -> tuple:
    """
    Extract AMSC code from NSN Details page and update rfq_index_extract.
    Also checks for closed solicitations and updates the closed field.
    
    Args:
        contract_id: The contract ID from universal_contract_queue
        nsn: The National Stock Number to look up
        
    Returns:
        tuple: (success: bool, amsc_code: str, is_closed: bool)
            - success: True if workflow completed successfully, False if failed
            - amsc_code: The actual AMSC code value (e.g., 'G', 'A', 'B', etc.)
            - is_closed: True if no open solicitations found, False if open solicitations exist
            
    Note: Using tuple instead of tuple[bool, str, bool] for Python 3.8 compatibility
    """
    try:
        logger.info(f"Starting AMSC extraction for contract {contract_id}, NSN: {nsn}")
        
        # Initialize scraper and uploader
        logger.info("Initializing DibbsScraper...")
        scraper = DibbsScraper()
        logger.info("DibbsScraper initialized successfully")
        
        logger.info("Initializing SupabaseUploader...")
        uploader = SupabaseUploader()
        logger.info("SupabaseUploader initialized successfully")
        
        # Log environment variables (without sensitive values)
        import os
        logger.info(f"Environment variables available:")
        logger.info(f"  VITE_SUPABASE_URL: {'Set' if os.getenv('VITE_SUPABASE_URL') else 'Not set'}")
        logger.info(f"  SUPABASE_SERVICE_ROLE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'Not set'}")
        logger.info(f"  DIBBS_BASE_URL: {os.getenv('DIBBS_BASE_URL', 'Not set')}")
        
        # First, check if there are open RFQ solicitations for this NSN
        logger.info(f"Checking closed status for NSN: {nsn}")
        is_closed = scraper.check_nsn_closed_status(nsn)
        
        if is_closed is None:
            logger.warning(f"Could not determine closed status for NSN: {nsn}")
            is_closed = False  # Default to open if we can't determine
        
        logger.info(f"NSN {nsn} closed status: {is_closed}")
        
        # Update the closed field in rfq_index_extract
        if is_closed:
            logger.info(f"Updating closed status to True for contract {contract_id}")
            closed_update_success = uploader.update_rfq_closed_status(contract_id, True)
            if not closed_update_success:
                logger.warning(f"Failed to update closed status for contract {contract_id}")
        else:
            logger.info(f"Updating closed status to False for contract {contract_id}")
            closed_update_success = uploader.update_rfq_closed_status(contract_id, False)
            if not closed_update_success:
                logger.warning(f"Failed to update closed status for contract {contract_id}")
        
        # Extract AMSC code from NSN Details page
        logger.info(f"Calling scraper.extract_nsn_amsc for NSN: {nsn}")
        amsc_code = scraper.extract_nsn_amsc(nsn)
        
        if amsc_code is None:
            logger.error(f"Failed to extract AMSC code for NSN: {nsn}")
            return (False, "", is_closed)
        
        logger.info(f"Extracted AMSC code: {amsc_code}")
        
        # Update the rfq_index_extract table with the actual AMSC code
        logger.info(f"Attempting to update rfq_index_extract for contract {contract_id} with cde_g: {amsc_code}")
        success = uploader.update_rfq_amsc(contract_id, amsc_code)
        
        if success:
            logger.info(f"Successfully updated rfq_index_extract for contract {contract_id} with cde_g: {amsc_code}")
            return (True, amsc_code, is_closed)
        else:
            logger.error(f"Failed to update rfq_index_extract for contract {contract_id}")
            return (False, amsc_code, is_closed)
            
    except Exception as e:
        logger.error(f"Error in extract_nsn_amsc: {str(e)}")
        return (False, "", False)

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Extract AMSC code from NSN Details page")
    parser.add_argument("contract_id", help="Contract ID from universal_contract_queue")
    parser.add_argument("nsn", help="National Stock Number to look up")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success, amsc_level, is_closed = extract_nsn_amsc(args.contract_id, args.nsn)
    
    if success:
        logger.info(f"AMSC extraction completed successfully. AMSC code: {amsc_level}, Closed: {is_closed}")
        sys.exit(0)
    else:
        logger.error("AMSC extraction failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
