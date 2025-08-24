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

def extract_nsn_amsc(contract_id: str, nsn: str) -> tuple:
    """
    Extract AMSC code from NSN Details page and update contract queue.
    
    Args:
        contract_id: The contract ID from universal_contract_queue
        nsn: The National Stock Number to look up
        
    Returns:
        tuple: (success: bool, is_g_level: bool)
            - success: True if workflow completed successfully, False if failed
            - is_g_level: True if AMSC is G, False if not G
            
    Note: Using tuple instead of tuple[bool, bool] for Python 3.8 compatibility
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
        
        # Extract AMSC code from NSN Details page
        logger.info(f"Calling scraper.extract_nsn_amsc for NSN: {nsn}")
        amsc_code = scraper.extract_nsn_amsc(nsn)
        
        if amsc_code is None:
            logger.error(f"Failed to extract AMSC code for NSN: {nsn}")
            return (False, False)
        
        logger.info(f"Extracted AMSC code: {amsc_code}")
        
        # Determine if AMSC is G
        is_g_level = amsc_code.upper() == 'G'
        logger.info(f"AMSC code '{amsc_code}' is G-level: {is_g_level}")
        
        # Update the contract queue with the result
        logger.info(f"Attempting to update contract {contract_id} with cde_g: {is_g_level}")
        success = uploader.update_contract_amsc(contract_id, is_g_level)
        
        if success:
            logger.info(f"Successfully updated contract {contract_id} with cde_g: {is_g_level}")
            logger.info(f"Database update completed successfully")
            return (True, is_g_level)  # Success, and here's the AMSC level
        else:
            logger.error(f"Failed to update contract {contract_id} with AMSC data")
            logger.error(f"Database update failed")
            return (False, False)  # Failed, no AMSC level
            
    except Exception as e:
        logger.error(f"Error in AMSC extraction workflow: {str(e)}")
        return (False, False)

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
    logger.info(f"Starting AMSC extraction workflow execution...")
    success, amsc_level = extract_nsn_amsc(args.contract_id, args.nsn)
    
    logger.info(f"Workflow execution completed - Success: {success}, AMSC Level: {amsc_level}")
    
    if success:
        logger.info(f"AMSC extraction completed successfully. AMSC is G-level: {amsc_level}")
        print(f"✅ AMSC extraction completed successfully!")
        print(f"   AMSC Code Level: {'G' if amsc_level else 'Not G'}")
        print(f"   Database Updated: Yes")
    else:
        logger.error("AMSC extraction failed")
        print("❌ AMSC extraction failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
