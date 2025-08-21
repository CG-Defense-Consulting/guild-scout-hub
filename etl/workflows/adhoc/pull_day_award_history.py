#!/usr/bin/env python3
"""
Pull Day Award History
Grabs the RFQ PDFs batch given a day and parses award history
"""

import argparse
import logging
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.scrapers.dibbs_scraper import DibbsScraper
from core.processors.award_processor import AwardProcessor
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def pull_day_award_history(target_date: date, 
                          output_dir: Optional[str] = None,
                          max_solicitations: Optional[int] = None,
                          force_refresh: bool = False) -> bool:
    """
    Pull award history for batch of solicitations for a given day.
    
    Args:
        target_date: The date to pull award history for
        output_dir: Optional output directory for PDFs
        max_solicitations: Maximum number of solicitations to process (None for all)
        force_refresh: Whether to force refresh even if award history exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting to pull award history for date: {target_date}")
        
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
        successful_awards = 0
        failed_awards = 0
        skipped_awards = 0
        
        for i, solicitation in enumerate(solicitations, 1):
            try:
                solicitation_number = solicitation.get('number', 'Unknown')
                logger.info(f"Processing solicitation {i}/{len(solicitations)}: {solicitation_number}")
                
                # Check if award history already exists (unless force_refresh)
                if not force_refresh:
                    uploader = SupabaseUploader()
                    existing_award = uploader.check_award_history_exists(solicitation_number)
                    if existing_award:
                        logger.info(f"Award history already exists for {solicitation_number}, skipping")
                        skipped_awards += 1
                        continue
                
                # Download PDF
                pdf_path = scraper.download_rfq_pdf(solicitation, output_dir)
                
                if pdf_path:
                    # Process the PDF for award history
                    processor = AwardProcessor()
                    award_data = processor.extract_award_history(pdf_path, solicitation_number)
                    
                    if award_data:
                        # Upload award history to Supabase
                        uploader = SupabaseUploader()
                        if uploader.upload_award_history(award_data):
                            successful_awards += 1
                            logger.info(f"Successfully processed award history for {solicitation_number}")
                        else:
                            failed_awards += 1
                            logger.error(f"Failed to upload award history for {solicitation_number}")
                    else:
                        logger.warning(f"No award history found in PDF for {solicitation_number}")
                        # Still count as successful since we processed it
                        successful_awards += 1
                else:
                    failed_awards += 1
                    logger.error(f"Failed to download PDF for {solicitation_number}")
                    
            except Exception as e:
                failed_awards += 1
                logger.error(f"Error processing solicitation {solicitation_number}: {str(e)}")
                continue
        
        # Summary
        logger.info(f"Award history batch processing completed. "
                   f"Successful: {successful_awards}, Failed: {failed_awards}, Skipped: {skipped_awards}")
        
        return failed_awards == 0 or successful_awards > 0
        
    except Exception as e:
        logger.error(f"Error in pull_day_award_history: {str(e)}")
        return False

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull batch of award history for a given day")
    parser.add_argument("date", help="Date to pull award history for (YYYY-MM-DD)")
    parser.add_argument("--output-dir", "-o", help="Output directory for PDFs")
    parser.add_argument("--max-solicitations", "-m", type=int, 
                       help="Maximum number of solicitations to process")
    parser.add_argument("--force-refresh", "-f", action="store_true", 
                       help="Force refresh even if award history exists")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    success = pull_day_award_history(target_date, args.output_dir, args.max_solicitations, args.force_refresh)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
