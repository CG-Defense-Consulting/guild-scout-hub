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
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Unit type mapping for parsing
UNIT_TYPE_MAPPING = {
    'AM': 'AMPOULE',
    'AT': 'ASSORTMENT',
    'AY': 'ASSEMBLY',
    'BA': 'BALL',
    'BD': 'BUNDLE',
    'BE': 'BALE',
    'BF': 'BOARD FOOT',
    'BG': 'BAG',
    'BK': 'BOOK',
    'BL': 'BARREL',
    'BO': 'BOLT',
    'BR': 'BAR',
    'BT': 'BOTTLE',
    'BX': 'BOX',
    'CA': 'CARTRIDGE',
    'CB': 'CARBOY',
    'CD': 'CUBIC YARD',
    'CE': 'CONE',
    'CF': 'CUBIC FOOT',
    'CK': 'CAKE',
    'CL': 'COIL',
    'CM': 'CENTIMETER',
    'CN': 'CAN',
    'CO': 'CONTAINER',
    'CS': 'CASE',
    'CT': 'CARTON',
    'CU': 'CUBE',
    'CY': 'CYLINDER',
    'CZ': 'CUBIC METER',
    'DR': 'DRUM',
    'DZ': 'DOZEN',
    'EA': 'EACH',
    'EN': 'ENVELOPE',
    'FT': 'FOOT',
    'FV': 'FIVE',
    'FY': 'FIFTY',
    'GL': 'GALLON',
    'GP': 'GROUP',
    'GR': 'GROSS',
    'HD': 'HUNDRED (100)',
    'HK': 'HANK',
    'IN': 'INCH',
    'JR': 'JAR',
    'KG': 'KILOGRAM',
    'KT': 'KIT',
    'LB': 'POUND',
    'LG': 'LENGTH',
    'LI': 'LITER',
    'LT': 'LOT',
    'MC': 'THOUSAND CUBIC FEET',
    'ME': 'MEAL',
    'MM': 'MILLIMETER',
    'MR': 'METER',
    'MX': 'THOUSAND (1000)',
    'OT': 'OUTFIT',
    'OZ': 'OUNCE',
    'PD': 'PAD',
    'PG': 'PACKAGE',
    'PK': 'PACKAGE BUY',
    'PM': 'PLATE',
    'PR': 'PAIR',
    'PT': 'PINT',
    'PZ': 'PACKET',
    'QT': 'QUART',
    'RA': 'RATION',
    'RL': 'REEL',
    'RM': 'REAM (500 SHEETS)',
    'RO': 'ROLL',
    'SD': 'SKID',
    'SE': 'SET',
    'SF': 'SQUARE FOOT',
    'SH': 'SHEET',
    'SK': 'SKIEN',
    'SL': 'SPOOL',
    'SO': 'SHOT',
    'SP': 'STRIP',
    'SV': 'SERVICE',
    'SX': 'STICK',
    'SY': 'SQUARE YARD',
    'TD': 'TWENTY-FOUR',
    'TE': 'TEN',
    'TF': 'TWENTY-FIVE',
    'TN': 'TON',
    'TO': 'TROY OUNCE',
    'TS': 'THIRTY-SIX',
    'TU': 'TUBE',
    'VI': 'VIAL',
    'XX': 'DOLLARS FOR SERVICES',
    'YD': 'YARD'
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
    Parse the index.txt file using the correct parsing logic for DIBBS format.
    
    Real format analysis shows each line is 140 characters with this structure:
    SOLICITATION(13) + NSN(13) + SPACES + PRN(10) + DATE(8) + PDF_NAME + SPACES + QTY(7) + UNIT(2) + DESCRIPTION + CODES
    
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
        
        # Combine multi-line records (each logical record is split across 2 physical lines)
        combined_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if this line contains a solicitation number pattern (starts with SPE and is 13 chars)
            if line.startswith('SPE') and len(line) >= 13:
                # This is the start of a record, try to combine with next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith('SPE'):
                        # Combine the two lines
                        combined_line = line + next_line
                        combined_lines.append(combined_line)
                        i += 2  # Skip both lines
                        continue
                    else:
                        # Single line record
                        combined_lines.append(line)
                        i += 1
                        continue
                else:
                    # Last line, single record
                    combined_lines.append(line)
                    i += 1
                    continue
            else:
                # Skip lines that don't start with SPE
                i += 1
                continue
        
        # If no records were found with the SPE pattern, try alternative patterns
        if not combined_lines:
            logger.warning("No SPE-pattern records found, trying alternative parsing approaches...")
            
            # Debug: Log the first few lines to understand the file format
            logger.info(f"First 5 lines of file for debugging:")
            for i, line in enumerate(lines[:5]):
                logger.info(f"  Line {i+1}: '{line.strip()}' (length: {len(line.strip())})")
            
            # Look for any lines that contain .pdf (which should indicate RFQ data)
            pdf_lines = [line.strip() for line in lines if '.pdf' in line]
            if pdf_lines:
                logger.info(f"Found {len(pdf_lines)} lines with .pdf, attempting direct parsing")
                combined_lines = pdf_lines
            else:
                # Look for lines with typical RFQ patterns (numbers, dates, etc.)
                potential_rfq_lines = []
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 20:  # Reasonable length for RFQ data
                        # Check if line contains typical RFQ elements
                        if any(pattern in line for pattern in ['/', '.pdf', 'SPE', 'DLA', 'MIL']):
                            potential_rfq_lines.append(line)
                
                if potential_rfq_lines:
                    logger.info(f"Found {len(potential_rfq_lines)} potential RFQ lines")
                    combined_lines = potential_rfq_lines
                else:
                    logger.warning("No recognizable RFQ data patterns found in file")
                    # Debug: Log all lines to understand what we're working with
                    logger.info("All lines in file for debugging:")
                    for i, line in enumerate(lines):
                        if line.strip():  # Only log non-empty lines
                            logger.info(f"  Line {i+1}: '{line.strip()}' (length: {len(line.strip())})")
        
        logger.info(f"Combined into {len(combined_lines)} logical records")
        
        for line_num, line in enumerate(combined_lines, 1):
            try:
                # Each combined line should be approximately 140 characters (allowing for some variation)
                if len(line) < 100:  # Minimum reasonable length for a complete record
                    logger.warning(f"Line {line_num}: Too short ({len(line)} chars), skipping")
                    continue
                
                # Parse based on fixed positions
                solicitation_number = line[0:13].strip()  # Positions 0-12
                national_stock_number = line[13:26].strip()  # Positions 13-25
                
                # Find the PRN and date after the spaces
                # Look for the pattern: spaces + 10 digits + 8 digits (mm/dd/yy)
                import re
                
                # Find PRN (10 digits) and date (mm/dd/yy) pattern
                prn_date_match = re.search(r'\s+(\d{10})(\d{2}/\d{2}/\d{2})', line)
                if not prn_date_match:
                    logger.warning(f"Line {line_num}: Could not find PRN/date pattern, skipping")
                    continue
                
                purchase_request_number = prn_date_match.group(1)
                return_by_date = prn_date_match.group(2)
                
                # Find quantity and unit after .pdf
                if '.pdf' not in line:
                    logger.warning(f"Line {line_num}: No .pdf found, skipping")
                    continue
                
                # Split by .pdf and get the description part
                parts = line.split('.pdf')
                if len(parts) != 2:
                    logger.warning(f"Line {line_num}: Invalid .pdf split, skipping")
                    continue
                
                description_part = parts[1].strip()
                
                # Extract quantity (7 digits) and unit (2 letters)
                qty_unit_match = re.search(r'(\d{7})([A-Z]{2})', description_part)
                if not qty_unit_match:
                    logger.warning(f"Line {line_num}: Could not find quantity/unit pattern, skipping")
                    continue
                
                quantity_str = qty_unit_match.group(1)
                unit_type = qty_unit_match.group(2)
                
                # Convert quantity to integer, removing leading zeros
                quantity = int(quantity_str.lstrip('0') or '0')
                
                # Get unit type description
                unit_type_long = UNIT_TYPE_MAPPING.get(unit_type, 'Unknown')
                
                # Extract description (everything after unit type)
                description_start = description_part.find(unit_type) + 2
                description = description_part[description_start:].strip()
                
                # The description format is: ITEM+DESCRIPTION(20 chars) + SPACE(1) + ALPHANUMERIC_CODE(9-12 chars)
                # Extract the first 20 characters for item + description
                if len(description) >= 21:  # At least 20 chars + 1 space + some code
                    item_description_part = description[:20].strip()
                    # The remaining part after 20 chars + 1 space is the alphanumeric code
                    alphanumeric_code = description[21:].strip()
                else:
                    item_description_part = description
                    alphanumeric_code = ''
                
                # Split item_description_part into item and additional description
                if ',' in item_description_part:
                    item, *additional_desc = item_description_part.split(',')
                    additional_description = ','.join(additional_desc).strip()
                else:
                    item = item_description_part
                    additional_description = ''
                
                parsed_row = [
                    solicitation_number,
                    national_stock_number,
                    purchase_request_number,
                    return_by_date,
                    quantity,
                    unit_type,
                    unit_type_long,
                    item,
                    additional_description,
                    alphanumeric_code,  # Add the alphanumeric code as a separate field
                    line  # raw row
                ]
                
                parsed_rows.append(parsed_row)
                logger.debug(f"Line {line_num}: Parsed successfully - SN: {solicitation_number}, NSN: {national_stock_number}, QTY: {quantity}, UNIT: {unit_type}")
                
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
            'timeout': timeout,
            'chrome_driver': chrome_driver
        }, {})
        
        if not nav_result.success:
            raise Exception(f"Archive navigation failed: {nav_result.error}")
        
        logger.info("✅ Archive page navigation completed")
        
        # Step 3: Handle consent page using the ConsentPageOperation
        logger.info("Step 3: Handling consent page")
        try:
            consent_op = ConsentPageOperation()
            consent_result = consent_op._execute({
                'timeout': timeout,
                'retry_attempts': 3,
                'base_url': 'https://dibbs2.bsm.dla.mil',
                'handle_current_page': True  # Handle consent on current page, don't navigate
            }, {'chrome_driver': chrome_driver})
            
            if consent_result.success:
                logger.info("✅ Consent page handled successfully")
                
                # Wait for the page to redirect and show actual text content
                # This is critical - after consent, we need to wait for the text to appear
                logger.info("⏳ Waiting for consent redirect to complete...")
                
                # Wait up to 10 seconds for the page to show text content
                max_wait = 10
                wait_time = 0
                while wait_time < max_wait:
                    time.sleep(1)
                    wait_time += 1
                    
                    # Check if we now have text content (not HTML)
                    page_source = chrome_driver.page_source
                    if not (page_source.startswith('<!DOCTYPE html') or '<html' in page_source):
                        logger.info(f"✅ Text content appeared after {wait_time} seconds")
                        break
                    elif 'Department of Defense' not in page_source and 'Notice and Consent' not in page_source:
                        logger.info(f"✅ Consent page redirected after {wait_time} seconds")
                        break
                    else:
                        logger.info(f"⏳ Still on consent page, waiting... ({wait_time}/{max_wait}s)")
                
                if wait_time >= max_wait:
                    logger.warning("⚠️ Timeout waiting for consent redirect")
                    
            else:
                logger.warning(f"⚠️ Consent page handling failed: {consent_result.error}")
                # Continue with workflow even if consent handling fails
                
        except Exception as e:
            logger.warning(f"⚠️ Consent page handling failed: {str(e)}")
            # Continue with workflow even if consent handling fails
        
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
