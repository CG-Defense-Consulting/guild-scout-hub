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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations.chrome_setup_operation import ChromeSetupOperation
from core.operations.archive_downloads_navigation_operation import ArchiveDownloadsNavigationOperation
from core.operations.consent_page_operation import ConsentPageOperation
from core.operations.dibbs_text_file_download_operation import DibbsTextFileDownloadOperation
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Unit type mapping for parsing
UNIT_TYPE_MAPPING = {
    'EA': 'Each',
    'FT': 'Foot',
    'IN': 'Inch',
    'LB': 'Pound',
    'YD': 'Yard',
    'GA': 'Gallon',
    'PR': 'Pair',
    'UN': 'Unit',
    'BG': 'Bag',
    'BX': 'Box',
    'CA': 'Case',
    'CT': 'Count',
    'DR': 'Dozen',
    'PK': 'Pack',
    'RL': 'Roll',
    'ST': 'Set',
    'TK': 'Tank',
    'TU': 'Tube',
    'WA': 'Watt',
    'WH': 'Watt Hour'
}

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
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def parse_index_file(file_path: str) -> List[List[str]]:
    """
    Parse the index.txt file using the specific parsing logic.
    
    Args:
        file_path: Path to the downloaded index.txt file
        
    Returns:
        List of parsed rows with extracted data
    """
    try:
        logger.info(f"Parsing index file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Index file not found: {file_path}")
        
        parsed_rows = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        logger.info(f"Read {len(lines)} lines from index file")
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                # Apply the specific parsing logic
                row = line[:-11].strip().split('.pdf')
                
                if len(row) != 2:
                    logger.warning(f"Line {line_num}: Invalid format, skipping")
                    continue
                
                part_1 = row[0].replace(' ', '')
                part_2 = row[1].strip()
                
                solicitation_number = part_1[:13]  # SN is 13 digits
                
                shift = 0 if '-' not in part_1[:40] else 1
                
                national_stock_number = part_1[13:26 + shift]  # NSN is 13 digits
                purchase_request_number = part_1[26 + shift: 36 + shift]  # PRN is 10 digits
                
                return_by_date = part_1[36 + shift: 44 + shift]  # 8 digits -- mm/dd/yy
                
                quantity = int(part_2[:7])  # 7 digit int
                unit_type = part_2[7:9]  # 2 digit code
                unit_type_long = UNIT_TYPE_MAPPING.get(unit_type, 'Unknown')
                
                item, *desc = part_2[9:].split(',')
                
                parsed_row = [
                    solicitation_number,
                    national_stock_number,
                    purchase_request_number,
                    return_by_date,
                    quantity,
                    unit_type,
                    unit_type_long,
                    item, 
                    ','.join(desc).strip(),
                    row[0] + row[1]  # raw row
                ]
                
                parsed_rows.append(parsed_row)
                logger.debug(f"Line {line_num}: Parsed successfully - SN: {solicitation_number}, NSN: {national_stock_number}")
                
            except Exception as e:
                logger.warning(f"Line {line_num}: Parsing error: {str(e)}, skipping")
                continue
        
        logger.info(f"Successfully parsed {len(parsed_rows)} rows from index file")
        return parsed_rows
        
    except Exception as e:
        logger.error(f"Error parsing index file: {str(e)}")
        raise

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
            'timeout': timeout
        }, {'chrome_driver': chrome_driver})
        
        if not nav_result.success:
            raise Exception(f"Archive navigation failed: {nav_result.error}")
        
        logger.info("✅ Archive page navigation completed")
        
        # Step 3: Handle consent page
        logger.info("Step 3: Handling consent page")
        consent_op = ConsentPageOperation()
        consent_result = consent_op._execute({
            'timeout': timeout,
            'retry_attempts': 3,
            'base_url': 'https://www.dibbs.bsm.dla.mil'
        }, {'chrome_driver': chrome_driver})
        
        if consent_result.success:
            logger.info("✅ Consent page handled successfully")
        else:
            logger.warning(f"⚠️ Consent page handling failed: {consent_result.error}")
        
        # Step 4: Download index.txt file
        logger.info("Step 4: Downloading index.txt file")
        download_op = DibbsTextFileDownloadOperation()
        download_result = download_op._execute({
            'timeout': timeout,
            'retry_attempts': 3
        }, {'chrome_driver': chrome_driver})
        
        if not download_result.success:
            raise Exception(f"Index file download failed: {download_result.error}")
        
        file_path = download_result.data.get('file_path')
        logger.info(f"✅ Index file downloaded: {file_path}")
        
        # Step 5: Parse index.txt file
        logger.info("Step 5: Parsing index.txt file")
        parsed_data = parse_index_file(file_path)
        
        if not parsed_data:
            logger.warning("⚠️ No data parsed from index file")
            return {
                'success': True,
                'date_processed': date_to_process,
                'records_processed': 0,
                'file_path': file_path,
                'message': 'No data to process'
            }
        
        logger.info(f"✅ Index file parsed: {len(parsed_data)} records extracted")
        
        # Step 6: Upload to Supabase
        logger.info("Step 6: Uploading to Supabase")
        upload_op = SupabaseUploadOperation()
        
        # Prepare data for upload
        upload_data = []
        for row in parsed_data:
            upload_data.append({
                'solicitation_number': row[0],
                'national_stock_number': row[1],
                'purchase_request_number': row[2],
                'return_by_date': row[3],
                'quantity': row[4],
                'unit_type': row[5],
                'unit_type_long': row[6],
                'item': row[7],
                'description': row[8],
                'raw_row': row[9],
                'processed_date': date_to_process,
                'processed_at': 'now()'
            })
        
        upload_result = upload_op._execute({
            'results': upload_data,
            'table_name': 'rfq_index_extract',
            'operation_type': 'upsert',
            'upsert_strategy': 'merge',
            'conflict_resolution': 'update_existing',
            'key_fields': ['solicitation_number', 'national_stock_number'],
            'batch_size': 50
        }, {})
        
        if upload_result.success:
            logger.info(f"✅ Supabase upload completed: {len(upload_data)} records")
        else:
            raise Exception(f"Supabase upload failed: {upload_result.error}")
        
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
        sys.exit(0)
    else:
        logger.error(f"❌ DIBBS RFQ Index Pull workflow failed: {result.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
