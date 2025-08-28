#!/usr/bin/env python3
"""
DIBBS RFQ Index Scheduled Data Pull Workflow

This workflow runs daily at 2:30 AM to:
1. Navigate to the DIBBS archive downloads page for a specific date
2. Handle consent pages if they appear
3. Download the RFQ index text file
4. Parse the text file using the index processor
5. Upsert the parsed data to the rfq_index_extract table in Supabase
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the etl directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations.chrome_setup_operation import ChromeSetupOperation
from core.operations.archive_downloads_navigation_operation import ArchiveDownloadsNavigationOperation
from core.operations.consent_page_operation import ConsentPageOperation
from core.operations.dibbs_text_file_download_operation import DibbsTextFileDownloadOperation
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from core.processors.index_processor import IndexProcessor
from utils.logger import setup_logger

logger = logging.getLogger(__name__)


def get_target_date(date_input: str = None) -> str:
    """Get the target date for the archive download."""
    if date_input:
        try:
            datetime.strptime(date_input, '%Y-%m-%d')
            return date_input
        except ValueError:
            logger.warning(f"Invalid date format: {date_input}. Using yesterday's date instead.")
    
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def parse_text_file(file_path: str) -> list:
    """Parse the downloaded text file and return structured data."""
    logger.info(f"Parsing text file: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Text file not found: {file_path}")
    
    processor = IndexProcessor()
    parsed_data = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
        # Skip header lines (starting with #)
        data_lines = [line.strip() for line in lines if not line.strip().startswith('#') and line.strip()]
        
        # Parse each line (assuming CSV-like format)
        for line in data_lines:
            if line:
                parts = line.split(',')
                if len(parts) >= 4:
                    solicitation_info = {
                        "nsn": parts[0].strip(),
                        "amsc": parts[1].strip(),
                        "status": parts[2].strip(),
                        "description": parts[3].strip(),
                        "source_file": file_path,
                        "processed_at": datetime.now().isoformat()
                    }
                    
                    # Process using the index processor
                    processed_data = processor.process_solicitation_info(solicitation_info)
                    parsed_data.append(processed_data)
    
    logger.info(f"Successfully parsed {len(parsed_data)} records")
    return parsed_data


def execute_dibbs_rfq_index_workflow(target_date: str = None) -> dict:
    """
    Execute the DIBBS RFQ index pull workflow.
    
    Args:
        target_date: Target date for archive download (YYYY-MM-DD format)
        
    Returns:
        Dictionary with workflow results
    """
    date_to_process = get_target_date(target_date)
    logger.info(f"Starting DIBBS RFQ Index workflow for date: {date_to_process}")
    
    try:
        # Step 1: Setup Chrome
        logger.info("Step 1: Setting up Chrome browser")
        chrome_op = ChromeSetupOperation()
        chrome_result = chrome_op._execute({"headless": True, "timeout": 30}, {})
        
        if not chrome_result.success:
            raise Exception(f"Chrome setup failed: {chrome_result.error}")
        
        chrome_driver = chrome_result.data.get('driver')
        logger.info("✅ Chrome setup completed")
        
        # Step 2: Navigate to archive downloads page
        logger.info("Step 2: Navigating to archive downloads page")
        nav_op = ArchiveDownloadsNavigationOperation()
        nav_result = nav_op._execute({
            "date": date_to_process,
            "chrome_driver": chrome_driver,
            "base_url": "https://dibbs2.bsm.dla.mil",
            "timeout": 30
        }, {})
        
        if not nav_result.success:
            raise Exception(f"Archive navigation failed: {nav_result.error}")
        
        logger.info("✅ Archive navigation completed")
        
        # Step 3: Handle consent page if present
        logger.info("Step 3: Handling consent page")
        consent_op = ConsentPageOperation()
        consent_result = consent_op._execute({
            "nsn": "archive_download",
            "timeout": 30,
            "retry_attempts": 3,
            "base_url": "https://dibbs2.bsm.dla.mil"
        }, {"chrome_driver": chrome_driver})
        
        if not consent_result.success:
            logger.warning(f"Consent page handling failed: {consent_result.error}")
        else:
            logger.info("✅ Consent page handled")
        
        # Step 4: Download text file
        logger.info("Step 4: Downloading text file")
        download_op = DibbsTextFileDownloadOperation()
        download_result = download_op._execute({
            "dibbs_base_url": "https://dibbs2.bsm.dla.mil",
            "download_dir": os.getenv("DIBBS_DOWNLOAD_DIR", "./downloads"),
            "file_type": "rfq_index",
            "target_filename": f"dibbs_rfq_index_{date_to_process.replace('-', '')}"
        }, {})
        
        if not download_result.success:
            raise Exception(f"Text file download failed: {download_result.error}")
        
        file_path = download_result.data['file_path']
        logger.info(f"✅ Text file downloaded: {file_path}")
        
        # Step 5: Parse text file
        logger.info("Step 5: Parsing text file")
        parsed_data = parse_text_file(file_path)
        logger.info("✅ Text file parsing completed")
        
        # Step 6: Upload to Supabase
        logger.info("Step 6: Uploading data to Supabase")
        upload_op = SupabaseUploadOperation()
        
        # Prepare results in the format expected by SupabaseUploadOperation
        results = []
        for record in parsed_data:
            results.append({
                'success': True,
                'data': record
            })
        
        upload_result = upload_op._execute({
            "results": results,
            "table_name": "rfq_index_extract",
            "operation_type": "upsert",
            "upsert_strategy": "merge",
            "conflict_resolution": "update_existing",
            "key_fields": ["nsn"],
            "batch_size": 50
        }, {})
        
        if not upload_result.success:
            raise Exception(f"Supabase upload failed: {upload_result.error}")
        
        logger.info("✅ Supabase upload completed")
        
        # Workflow completed successfully
        return {
            "success": True,
            "date_processed": date_to_process,
            "records_processed": len(parsed_data),
            "file_path": file_path,
            "upload_result": upload_result.data
        }
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "date_processed": date_to_process
        }


def main():
    """Main entry point for the DIBBS RFQ index pull workflow."""
    parser = argparse.ArgumentParser(description="DIBBS RFQ Index Scheduled Data Pull")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh even if data exists")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--date", help="Target date for archive download (YYYY-MM-DD format, defaults to yesterday)")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logger(level=log_level)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get target date
    target_date = args.date or os.getenv("TARGET_DATE")
    
    logger.info("Starting DIBBS RFQ Index Scheduled Data Pull Workflow")
    
    # Execute the workflow
    result = execute_dibbs_rfq_index_workflow(target_date)
    
    if result["success"]:
        logger.info("🎉 Workflow completed successfully!")
        logger.info(f"Processed {result['records_processed']} records for date {result['date_processed']}")
        sys.exit(0)
    else:
        logger.error("❌ Workflow failed")
        logger.error(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
