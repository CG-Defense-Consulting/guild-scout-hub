#!/usr/bin/env python3
"""
DIBBS RFQ Index Pull Workflow

This workflow downloads and processes the daily RFQ index file from DIBBS.
It follows these steps:
1. Setup chromedriver
2. Navigate to archive page
3. Handle consent page
4. Download index.txt
5. Parse index.txt file
6. Upload to supabase
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations.chrome_setup_operation import ChromeSetupOperation
from core.operations.archive_downloads_navigation_operation import ArchiveDownloadsNavigationOperation
from core.operations.consent_page_operation import ConsentPageOperation
from core.operations.dibbs_text_file_download_operation import DibbsTextFileDownloadOperation
from core.operations.dibbs_text_file_parsing_operation import DibbsTextFileParsingOperation
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from utils.logger import setup_logger

logger = setup_logger(__name__)



def get_target_date(target_date: Optional[str] = None) -> str:
    """
    Get the target date for processing.
    
    Args:
        target_date: Optional specific date in YYYY-MM-DD format
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    if target_date:
        return target_date
    
    # Default to yesterday for scheduled runs
    yesterday = datetime.now() - timedelta(days=2)
    return yesterday.strftime('%Y-%m-%d')



def execute_dibbs_rfq_index_workflow(
    headless: bool = True,
    timeout: int = 30,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the DIBBS RFQ Index Pull workflow.
    
    Args:
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        target_date: Optional specific date for processing
        
    Returns:
        Dictionary containing workflow results
    """
    try:
        logger.info("🚀 Starting DIBBS RFQ Index Pull Workflow")
        
        # Get target date
        date_to_process = get_target_date(target_date)
        logger.info(f"Processing date: {date_to_process}")
        
        # Step 1: Setup Chrome driver
        logger.info("Step 1: Setting up Chrome driver")
        chrome_op = ChromeSetupOperation(headless=headless)
        chrome_result = chrome_op._execute({"headless": headless, "timeout": timeout}, {})
        
        if not chrome_result.success:
            raise Exception(f"Chrome setup failed: {chrome_result.error}")
        
        chrome_driver = chrome_result.data.get('driver')
        logger.info("✅ Chrome driver setup completed")
        
        # Step 2: Navigate to archive page
        logger.info("Step 2: Navigating to archive page")
        archive_nav_op = ArchiveDownloadsNavigationOperation()
        nav_result = archive_nav_op._execute({
            'target_date': date_to_process,
            'timeout': timeout,
            'chrome_driver': chrome_driver
        }, {})
        
        if not nav_result.success:
            raise Exception(f"Archive navigation failed: {nav_result.error}")
        
        logger.info("✅ Archive page navigation completed")
        
        # Step 3: Check for and handle consent banner if present
        logger.info("Step 3: Checking for consent banner")
        
        # try:
        consent_op = ConsentPageOperation()
        consent_result = consent_op._execute({
            'timeout': timeout,
            'retry_attempts': 3,
        }, {'chrome_driver': chrome_driver})
        
        if consent_result.success:
            logger.info("✅ Consent banner handled successfully")
        else:
            # raise an exception
            raise Exception(f"Consent banner handling failed: {consent_result.error}")
                
        # except Exception as e:
        #     logger.warning(f"⚠️ Consent banner handling failed: {str(e)}")
        
        # Step 4: Download index.txt file
        logger.info("Step 4: Downloading index.txt file")
        
        # Create a generic download directory that works in both local and GitHub Actions environments
        if os.getenv('GITHUB_ACTIONS'):
            # GitHub Actions environment
            download_dir = '/tmp/downloads'
        else:
            # Local environment - use a relative path that works from project root
            download_dir = os.path.join(os.getcwd(), 'downloads')
        
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"Using download directory: {download_dir}")
        
        download_op = DibbsTextFileDownloadOperation()
        download_result = download_op._execute({
            'timeout': timeout,
            'retry_attempts': 3,
            'download_dir': download_dir
        }, {'chrome_driver': chrome_driver})
        
        if not download_result.success:
            raise Exception(f"Index file download failed: {download_result.error}")
        
        file_path = download_result.data.get('file_path')
        logger.info(f"✅ Index file downloaded: {file_path}")
        
        # Step 5: Parse index.txt file
        logger.info("Step 5: Parsing index.txt file")
        
        # Use the new DibbsTextFileParsingOperation
        parsing_op = DibbsTextFileParsingOperation()
        parsing_result = parsing_op._execute({
            'file_path': file_path,
            'encoding': 'utf-8',
            'errors': 'ignore'
        }, {})
        
        if not parsing_result.success:
            raise Exception(f"Index file parsing failed: {parsing_result.error}")
        
        parsed_data = parsing_result.data.get('parsed_rows', [])
        print(parsed_data[0])
        
        if not parsed_data:
            logger.warning("⚠️ No data parsed from index file")
            return {
                'success': True,
                'date_processed': date_to_process,
                'records_processed': 0,
                'file_path': file_path,
                'message': 'No data to process'
            }
        
        # logger.info(f"✅ Index file parsed: {len(parsed_data)} records extracted")
        # logger.info(f"📊 Parsing operation metadata: {parsing_result.metadata}")
        
        # # Step 6: Upload to Supabase
        logger.info("Step 6: Uploading to Supabase")
        upload_op = SupabaseUploadOperation()
        
        # Prepare data for upload using structured data from the operation
        upload_data = []
        structured_data = parsing_result.data.get('structured_data', [])
        
        for row_data in structured_data:
            upload_data.append({
                'solicitation_number': row_data['solicitation_number'],
                'national_stock_number': row_data['national_stock_number'],
                'purchase_request_number': row_data['purchase_request_number'],
                'return_by_date': row_data['return_by_date'],
                'quote_issue_date': date_to_process,  # Use the processing date in YYYY-mm-dd format
                'quantity': row_data['quantity'],
                'unit_type': row_data['unit_type'],
                'unit_type_long': row_data['unit_type_long'],
                'item': row_data['item'],
                'desc': row_data['description'],
                'raw': row_data['raw_row'],
                'closed': False
            })
        
        # print(upload_data[0])
        
        upload_result = upload_op._execute({
            'results': upload_data,
            'table_name': 'rfq_index_extract',
            'operation_type': 'upsert',
            'upsert_strategy': 'merge',
            'conflict_resolution': 'update_existing',
            'key_fields': ['solicitation_number', 'national_stock_number', 'purchase_request_number'],
            'batch_size': 50
        }, {})
        
        # if upload_result.success:
        #     logger.info(f"✅ Supabase upload completed: {len(upload_data)} records")
        # else:
        #     raise Exception(f"Supabase upload failed: {upload_result.data['upload_errors']}")
        
        # Cleanup
        try:
            if chrome_driver:
                chrome_driver.quit()
                logger.info("✅ Chrome driver cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Error during Chrome cleanup: {str(e)}")
        
        # Return results
        return {
            'success': True,
            'date_processed': date_to_process,
            'records_processed': len(parsed_data),
            'file_path': file_path,
            'parsing_result': {
                'total_records': parsing_result.data.get('total_records', 0),
                'parsing_method': parsing_result.metadata.get('parsing_method', 'unknown')
            },
            'upload_result': {
                'upserted_count': len(upload_data),
                'success': True
            },
            'message': 'DIBBS RFQ Index Pull workflow completed successfully'
        }
        
    except Exception as e:
        logger.error(f"❌ DIBBS RFQ Index Pull workflow failed: {str(e)}")
        
        # Cleanup on failure
        try:
            if 'chrome_driver' in locals() and chrome_driver:
                chrome_driver.quit()
                logger.info("✅ Chrome driver cleaned up after failure")
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Error during cleanup after failure: {str(cleanup_error)}")
        
        return {
            'success': False,
            'date_processed': target_date or get_target_date(),
            'error': str(e),
            'message': 'DIBBS RFQ Index Pull workflow failed'
        }

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Execute DIBBS RFQ Index Pull workflow")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode (default: True)")
    parser.add_argument("--with-head", action="store_false", default=False, dest='headless')
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for page operations in seconds (default: 30)")
    parser.add_argument("--target-date", help="Specific date to process (YYYY-MM-DD format, defaults to yesterday)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting DIBBS RFQ Index Pull workflow")
    
    # Execute workflow
    result = execute_dibbs_rfq_index_workflow(
        headless=args.headless,
        timeout=args.timeout,
        target_date=args.target_date
    )
    
    # Output results
    if result.get('success'):
        logger.info("🎉 DIBBS RFQ Index Pull workflow completed successfully")
        logger.info(f"Date processed: {result.get('date_processed')}")
        logger.info(f"Records processed: {result.get('records_processed')}")
        logger.info(f"File path: {result.get('file_path')}")
        
        # Log parsing operation details
        parsing_result = result.get('parsing_result', {})
        if parsing_result:
            logger.info(f"Parsing method: {parsing_result.get('parsing_method', 'unknown')}")
            logger.info(f"Total records from parsing: {parsing_result.get('total_records', 0)}")
        sys.exit(0)
    else:
        logger.error(f"❌ DIBBS RFQ Index Pull workflow failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
