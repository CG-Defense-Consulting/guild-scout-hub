#!/usr/bin/env python3
"""
Pull Day RFQ PDFs
Grabs the batch of RFQ PDFs for a given day from dibbs.bsm.dla.mil
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
from core.processors.pdf_processor import PDFProcessor
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)

def pull_day_rfq_pdfs(target_date: date, output_dir: Optional[str] = None, 
                      max_pdfs: Optional[int] = None) -> bool:
    """
    Pull batch of RFQ PDFs for a given day.
    
    Args:
        target_date: The date to pull RFQs for
        output_dir: Optional output directory for PDFs
        max_pdfs: Maximum number of PDFs to process (None for all)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting to pull RFQ PDFs for date: {target_date}")
        
        # Initialize scraper
        scraper = DibbsScraper()
        
        # Get list of solicitations for the day
        logger.info("Fetching solicitation list for the day...")
        solicitations = scraper.get_daily_solicitations(target_date)
        
        if not solicitations:
            logger.warning(f"No solicitations found for {target_date}")
            return True  # Not an error, just no data
            
        # Limit if max_pdfs specified
        if max_pdfs:
            solicitations = solicitations[:max_pdfs]
            logger.info(f"Processing {len(solicitations)} solicitations (limited by max_pdfs)")
        else:
            logger.info(f"Processing {len(solicitations)} solicitations")
        
        # Process each solicitation
        successful_downloads = 0
        failed_downloads = 0
        
        for i, solicitation in enumerate(solicitations, 1):
            try:
                logger.info(f"Processing solicitation {i}/{len(solicitations)}: {solicitation.get('number', 'Unknown')}")
                
                # Download PDF
                pdf_path = scraper.download_rfq_pdf(solicitation, output_dir)
                
                if pdf_path:
                    # Process the PDF
                    processor = PDFProcessor()
                    extracted_data = processor.extract_rfq_data(pdf_path)
                    
                    # Upload to Supabase
                    uploader = SupabaseUploader()
                    if uploader.upload_rfq_data(extracted_data):
                        successful_downloads += 1
                        logger.info(f"Successfully processed {solicitation.get('number', 'Unknown')}")
                    else:
                        failed_downloads += 1
                        logger.error(f"Failed to upload {solicitation.get('number', 'Unknown')}")
                else:
                    failed_downloads += 1
                    logger.error(f"Failed to download PDF for {solicitation.get('number', 'Unknown')}")
                    
            except Exception as e:
                failed_downloads += 1
                logger.error(f"Error processing solicitation {solicitation.get('number', 'Unknown')}: {str(e)}")
                continue
        
        # Summary
        logger.info(f"Batch processing completed. Successful: {successful_downloads}, Failed: {failed_downloads}")
        
        return failed_downloads == 0 or successful_downloads > 0
        
    except Exception as e:
        logger.error(f"Error in pull_day_rfq_pdfs: {str(e)}")
        return False

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull batch of RFQ PDFs for a given day")
    parser.add_argument("date", help="Date to pull RFQs for (YYYY-MM-DD)")
    parser.add_argument("--output-dir", "-o", help="Output directory for PDFs")
    parser.add_argument("--max-pdfs", "-m", type=int, help="Maximum number of PDFs to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format. Use YYYY-MM-DD")
        sys.exit(1)
    
    success = pull_day_rfq_pdfs(target_date, args.output_dir, args.max_pdfs)
    
    if success:
        logger.info("Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
