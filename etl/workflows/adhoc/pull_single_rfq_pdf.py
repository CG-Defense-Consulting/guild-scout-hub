#!/usr/bin/env python3
"""
Pull Single RFQ PDF
Grabs the RFQ PDF given a Solicitation Number from dibbs.bsm.dla.mil
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def pull_single_rfq_pdf(solicitation_number: str, output_dir: Optional[str] = None) -> bool:
    """
    Download a single RFQ PDF and upload it to Supabase storage.
    
    Args:
        solicitation_number: The solicitation number to search for
        output_dir: Optional output directory for the PDF
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting to pull RFQ PDF for solicitation: {solicitation_number}")
        
        # Initialize scraper
        scraper = DibbsScraper()
        
        # Search for the solicitation
        logger.info("Searching for solicitation...")
        solicitation_info = scraper.search_solicitation(solicitation_number)
        
        if not solicitation_info:
            logger.error(f"Solicitation {solicitation_number} not found")
            return False
            
        # Download the PDF
        logger.info("Downloading PDF...")
        pdf_path = scraper.download_rfq_pdf(solicitation_info, output_dir)
        
        if not pdf_path:
            logger.error("Failed to download PDF")
            return False
            
        # Upload PDF directly to Supabase storage
        logger.info("Uploading PDF to Supabase storage...")
        uploader = SupabaseUploader()
        success = uploader.upload_rfq_data(pdf_path, solicitation_number)
        
        if success:
            logger.info(f"Successfully processed and uploaded RFQ for {solicitation_number}")
            return True
        else:
            logger.error("Failed to upload to database")
            return False
            
    except Exception as e:
        logger.error(f"Error in pull_single_rfq_pdf: {str(e)}")
        return False

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull single RFQ PDF by solicitation number")
    parser.add_argument("solicitation_number", help="Solicitation number to search for")
    parser.add_argument("--output-dir", "-o", help="Output directory for PDF")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = pull_single_rfq_pdf(args.solicitation_number, args.output_dir)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
