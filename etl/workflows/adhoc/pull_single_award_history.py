#!/usr/bin/env python3
"""
Pull Single Award History
Grabs the RFQ PDF given a solicitation number and parses award history
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.processors.award_processor import AwardProcessor
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def pull_single_award_history(solicitation_number: str, 
                             output_dir: Optional[str] = None,
                             force_refresh: bool = False) -> bool:
    """
    Pull award history for a single solicitation.
    
    Args:
        solicitation_number: The solicitation number to search for
        output_dir: Optional output directory for the PDF
        force_refresh: Whether to force refresh even if award history exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting to pull award history for solicitation: {solicitation_number}")
        
        # Initialize scraper
        scraper = DibbsScraper()
        
        # Check if award history already exists (unless force_refresh)
        if not force_refresh:
            uploader = SupabaseUploader()
            existing_award = uploader.check_award_history_exists(solicitation_number)
            if existing_award:
                logger.info(f"Award history already exists for {solicitation_number}")
                return True
        
        # Search for the solicitation
        logger.info("Searching for solicitation...")
        solicitation_info = scraper.search_solicitation(solicitation_number)
        
        if not solicitation_info:
            logger.error(f"Solicitation {solicitation_number} not found")
            return False
            
        # Download the PDF
        logger.info("Downloading RFQ PDF...")
        pdf_path = scraper.download_rfq_pdf(solicitation_info, output_dir)
        
        if not pdf_path:
            logger.error("Failed to download PDF")
            return False
            
        # Process the PDF for award history
        logger.info("Processing PDF for award history...")
        processor = AwardProcessor()
        award_data = processor.extract_award_history(pdf_path, solicitation_number)
        
        if not award_data:
            logger.warning(f"No award history found in PDF for {solicitation_number}")
            return True  # Not an error, just no award data
            
        # Upload award history to Supabase
        logger.info("Uploading award history to database...")
        uploader = SupabaseUploader()
        success = uploader.upload_award_history(award_data)
        
        if success:
            logger.info(f"Successfully processed and uploaded award history for {solicitation_number}")
            return True
        else:
            logger.error("Failed to upload award history to database")
            return False
            
    except Exception as e:
        logger.error(f"Error in pull_single_award_history: {str(e)}")
        return False

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull award history for a single solicitation")
    parser.add_argument("solicitation_number", help="Solicitation number to search for")
    parser.add_argument("--output-dir", "-o", help="Output directory for PDF")
    parser.add_argument("--force-refresh", "-f", action="store_true", 
                       help="Force refresh even if award history exists")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = pull_single_award_history(args.solicitation_number, args.output_dir, args.force_refresh)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
