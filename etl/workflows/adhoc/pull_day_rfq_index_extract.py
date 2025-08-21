#!/usr/bin/env python3
"""
Pull Day RFQ Index Extract
Grabs the batch of new solicitation info for a given day from dibbs.bsm.dla.mil
"""

import argparse
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.processors.index_processor import IndexProcessor
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def pull_day_rfq_index_extract(target_date: date, 
                              include_details: bool = False,
                              max_solicitations: Optional[int] = None) -> bool:
    """
    Extract batch of solicitation information for a given day.
    
    Args:
        target_date: The date to extract solicitations for
        include_details: Whether to fetch detailed information for each solicitation
        max_solicitations: Maximum number of solicitations to process (None for all)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting to extract RFQ index for date: {target_date}")
        
        # Initialize scraper
        scraper = DibbsScraper()
        
        # Get list of solicitations for the day
        logger.info("Fetching solicitation list for the day...")
        solicitations = scraper.get_daily_solicitations(target_date)
        
        if not solicitations:
            logger.warning(f"No solicitations found for {target_date}")
            return True  # Not an error, just no data
            
        # Limit if max_solicitations specified
        if max_solicitations:
            solicitations = solicitations[:max_solicitations]
            logger.info(f"Processing {len(solicitations)} solicitations (limited by max_solicitations)")
        else:
            logger.info(f"Processing {len(solicitations)} solicitations")
        
        # Process each solicitation
        successful_extracts = 0
        failed_extracts = 0
        
        for i, solicitation in enumerate(solicitations, 1):
            try:
                logger.info(f"Processing solicitation {i}/{len(solicitations)}: {solicitation.get('number', 'Unknown')}")
                
                # Extract basic information
                basic_info = {
                    'solicitation_number': solicitation.get('number'),
                    'title': solicitation.get('title'),
                    'date_posted': target_date.isoformat(),
                    'status': solicitation.get('status'),
                    'agency': solicitation.get('agency'),
                    'url': solicitation.get('url')
                }
                
                # Extract additional details if requested
                if include_details:
                    logger.info(f"Fetching detailed information for {solicitation.get('number', 'Unknown')}")
                    detailed_info = scraper.get_solicitation_details(solicitation)
                    if detailed_info:
                        basic_info.update(detailed_info)
                
                # Process the extracted information
                processor = IndexProcessor()
                processed_data = processor.process_solicitation_info(basic_info)
                
                # Upload to Supabase
                uploader = SupabaseUploader()
                if uploader.upload_solicitation_index(processed_data):
                    successful_extracts += 1
                    logger.info(f"Successfully processed index for {solicitation.get('number', 'Unknown')}")
                else:
                    failed_extracts += 1
                    logger.error(f"Failed to upload index for {solicitation.get('number', 'Unknown')}")
                    
            except Exception as e:
                failed_extracts += 1
                logger.error(f"Error processing solicitation {solicitation.get('number', 'Unknown')}: {str(e)}")
                continue
        
        # Summary
        logger.info(f"Index extraction completed. Successful: {successful_extracts}, Failed: {failed_extracts}")
        
        return failed_extracts == 0 or successful_extracts > 0
        
    except Exception as e:
        logger.error(f"Error in pull_day_rfq_index_extract: {str(e)}")
        return False

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Extract batch of solicitation info for a given day")
    parser.add_argument("date", help="Date to extract solicitations for (YYYY-MM-DD)")
    parser.add_argument("--include-details", "-d", action="store_true", 
                       help="Include detailed information for each solicitation")
    parser.add_argument("--max-solicitations", "-m", type=int, 
                       help="Maximum number of solicitations to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    success = pull_day_rfq_index_extract(target_date, args.include_details, args.max_solicitations)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
