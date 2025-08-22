#!/usr/bin/env python3
"""
Extract NSN AMSC Code Workflow

This workflow accesses the NSN Details page for a contract, extracts the AMSC code,
and updates the universal_contract_queue table with the cde_g boolean field.
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

def extract_nsn_amsc(contract_id: str, nsn: str) -> bool:
    """
    Extract AMSC code from NSN Details page and update contract queue.
    
    Args:
        contract_id: The contract ID from universal_contract_queue
        nsn: The National Stock Number to look up
        
    Returns:
        bool: True if AMSC is G, False otherwise
    """
    try:
        logger.info(f"Starting AMSC extraction for contract {contract_id}, NSN: {nsn}")
        
        # Initialize scraper and uploader
        scraper = DibbsScraper()
        uploader = SupabaseUploader()
        
        # Extract AMSC code from NSN Details page
        amsc_code = scraper.extract_nsn_amsc(nsn)
        
        if amsc_code is None:
            logger.error(f"Failed to extract AMSC code for NSN: {nsn}")
            return False
        
        logger.info(f"Extracted AMSC code: {amsc_code}")
        
        # Determine if AMSC is G
        is_g_level = amsc_code.upper() == 'G'
        
        # Update the contract queue with the result
        success = uploader.update_contract_amsc(contract_id, is_g_level)
        
        if success:
            logger.info(f"Successfully updated contract {contract_id} with cde_g: {is_g_level}")
            return is_g_level
        else:
            logger.error(f"Failed to update contract {contract_id} with AMSC data")
            return False
            
    except Exception as e:
        logger.error(f"Error in AMSC extraction workflow: {str(e)}")
        return False

def main():
    """Main entry point for the workflow."""
    parser = argparse.ArgumentParser(description='Extract NSN AMSC Code')
    parser.add_argument('contract_id', help='Contract ID from universal_contract_queue')
    parser.add_argument('nsn', help='National Stock Number to look up')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting NSN AMSC extraction workflow")
    logger.info(f"Contract ID: {args.contract_id}")
    logger.info(f"NSN: {args.nsn}")
    
    # Run the workflow
    result = extract_nsn_amsc(args.contract_id, args.nsn)
    
    if result:
        logger.info(f"AMSC extraction completed successfully. AMSC is G-level: {result}")
        print(f"✅ AMSC extraction completed. AMSC is G-level: {result}")
    else:
        logger.error("AMSC extraction failed")
        print("❌ AMSC extraction failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
