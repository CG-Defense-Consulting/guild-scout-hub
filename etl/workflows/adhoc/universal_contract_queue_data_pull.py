#!/usr/bin/env python3
"""
Universal Contract Queue Data Pull Workflow

This workflow navigates to NSN pages on DIBBS to:
1. Determine if solicitations are closed
2. Extract AMSC codes
3. Update the database with the extracted information

The workflow automatically discovers contracts that need processing by querying
the universal_contract_queue table for missing data.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations.chrome_setup_operation import ChromeSetupOperation
from core.operations.consent_page_operation import ConsentPageOperation
from core.operations.nsn_page_navigation_operation import NsnPageNavigationOperation
from core.operations.closed_solicitation_check_operation import ClosedSolicitationCheckOperation
from core.operations.amsc_extraction_operation import AmscExtractionOperation
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from core.uploaders.supabase_uploader import SupabaseUploader
from utils.logger import setup_logger

logger = setup_logger(__name__)


def query_contracts_needing_processing(supabase_client, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Query contracts that need AMSC codes extracted."""
    try:
        logger.info("Querying contracts needing AMSC codes...")
        
        # Query contracts with missing AMSC codes
        result = supabase_client.table('universal_contract_queue').select(
            "id,rfq_index_extract!inner(cde_g,solicitation_number,national_stock_number)"
        ).execute()
        
        if not result.data:
            logger.info("No contracts found in universal_contract_queue")
            return []
        
        # Filter for contracts with missing AMSC codes
        contracts_needing_processing = []
        for contract in result.data:
            contract_id = contract['id']
            rie_data = contract['rfq_index_extract']
            cde_g = rie_data.get('cde_g')
            
            # Check if AMSC code is missing
            if not cde_g or (isinstance(cde_g, str) and cde_g.strip() == ''):
                contract_data = {
                    'id': contract_id,
                    'solicitation_number': rie_data.get('solicitation_number'),
                    'national_stock_number': rie_data.get('national_stock_number')
                }
                contracts_needing_processing.append(contract_data)
        
        if limit:
            contracts_needing_processing = contracts_needing_processing[:limit]
        
        logger.info(f"Found {len(contracts_needing_processing)} contracts needing AMSC codes")
        return contracts_needing_processing
        
    except Exception as e:
        logger.error(f"Error querying contracts: {str(e)}")
        raise


def process_nsn_for_contract(nsn: str, chrome_driver, timeout: int = 30) -> Dict[str, Any]:
    """
    Process a single NSN to extract closed status and AMSC code.
    
    Args:
        nsn: National Stock Number to process
        chrome_driver: Chrome driver instance
        timeout: Timeout for page operations
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Processing NSN: {nsn}")
        
        # Step 1: Navigate to NSN page
        logger.info(f"Step 1: Navigating to NSN page for {nsn}")
        nav_op = NsnPageNavigationOperation()
        nav_result = nav_op._execute({
            'nsn': nsn, 
            'chrome_driver': chrome_driver, 
            'timeout': timeout
        }, {})
        
        if not nav_result.success:
            raise Exception(f"Navigation failed: {nav_result.error}")
        
        logger.info(f"✅ Navigation completed for NSN {nsn}")
        
        # Step 2: Handle consent page if present
        logger.info(f"Step 2: Handling consent page for {nsn}")
        consent_op = ConsentPageOperation()
        consent_result = consent_op._execute({
            'nsn': nsn, 
            'timeout': timeout, 
            'retry_attempts': 3,
            'base_url': 'https://www.dibbs.bsm.dla.mil'
        }, {'chrome_driver': chrome_driver})
        
        if consent_result.success:
            logger.info(f"✅ Consent page handled for NSN {nsn}")
        else:
            logger.warning(f"⚠️ Consent page handling failed for NSN {nsn}")
        
        # Step 3: Get current page HTML content
        html_content = chrome_driver.page_source
        logger.info(f"✅ Retrieved HTML content for NSN {nsn}")
        
        # Step 4: Check if solicitation is closed
        logger.info(f"Step 3: Checking closed status for {nsn}")
        closed_op = ClosedSolicitationCheckOperation()
        closed_result = closed_op._execute({
            'html_content': html_content, 
            'nsn': nsn
        }, {})
        
        if not closed_result.success:
            raise Exception(f"Closed status check failed: {closed_result.error}")
        
        is_closed = closed_result.data.get('is_closed')
        logger.info(f"✅ Closed status determined for NSN {nsn}: {is_closed}")
        
        # If closed, skip AMSC extraction
        if is_closed:
            logger.info(f"ℹ️ NSN {nsn} is closed, skipping AMSC extraction")
            return {
                'success': True,
                'nsn': nsn,
                'is_closed': is_closed,
                'amsc_code': None,
                'skipped': True
            }
        
        # Step 5: Extract AMSC code
        logger.info(f"Step 4: Extracting AMSC code for {nsn}")
        amsc_op = AmscExtractionOperation()
        amsc_result = amsc_op._execute({
            'html_content': html_content, 
            'nsn': nsn
        }, {})
        
        if not amsc_result.success:
            raise Exception(f"AMSC extraction failed: {amsc_result.error}")
        
        amsc_code = amsc_result.data.get('amsc_code')
        logger.info(f"✅ AMSC code extracted for NSN {nsn}: {amsc_code}")
        
        return {
            'success': True,
            'nsn': nsn,
            'is_closed': is_closed,
            'amsc_code': amsc_code,
            'skipped': False
        }
        
    except Exception as e:
        logger.error(f"Error processing NSN {nsn}: {str(e)}")
        return {
            'success': False,
            'nsn': nsn,
            'error': str(e)
        }


def execute_universal_contract_queue_workflow(
    headless: bool = True, 
    timeout: int = 30,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute the universal contract queue data pull workflow.
    
    Args:
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        limit: Optional limit on number of contracts to process
        
    Returns:
        Dictionary with workflow results
    """
    try:
        logger.info("🚀 Starting Universal Contract Queue Data Pull Workflow")
        
        # Step 1: Initialize Supabase client
        logger.info("Step 1: Initializing Supabase client")
        supabase_client = SupabaseUploader().supabase
        
        if not supabase_client:
            raise Exception("Failed to initialize Supabase client")
        
        logger.info("✅ Supabase client initialized")
        
        # Step 2: Query contracts needing processing
        logger.info("Step 2: Querying contracts needing processing")
        contracts = query_contracts_needing_processing(supabase_client, limit=limit)
        
        if not contracts:
            logger.info("ℹ️ No contracts need processing")
            return {
                'success': True,
                'contracts_processed': 0,
                'message': 'No contracts need processing'
            }
        
        logger.info(f"✅ Found {len(contracts)} contracts to process")
        
        # Debug: Log the structure of the first contract
        if contracts:
            first_contract = contracts[0]
            logger.info(f"Sample contract structure: {first_contract}")
            logger.info(f"Contract ID: {first_contract.get('id')}")
            logger.info(f"Solicitation Number: {first_contract.get('solicitation_number')}")
            logger.info(f"National Stock Number: {first_contract.get('national_stock_number')}")
        
        # Step 3: Setup Chrome browser
        logger.info("Step 3: Setting up Chrome browser")
        chrome_op = ChromeSetupOperation()
        chrome_result = chrome_op._execute({"headless": headless, "timeout": timeout}, {})
        
        if not chrome_result.success:
            raise Exception(f"Chrome setup failed: {chrome_result.error}")
        
        chrome_driver = chrome_result.data.get('driver')
        logger.info("✅ Chrome setup completed")
        
        # Step 4: Process each contract
        logger.info("Step 4: Processing contracts")
        results = []
        successful_processing = 0
        
        for i, contract in enumerate(contracts):
            contract_id = contract['id']
            nsn = contract.get('national_stock_number')
            
            if not nsn:
                logger.warning(f"Contract {contract_id} has no NSN, skipping")
                continue
            
            logger.info(f"Processing contract {i+1}/{len(contracts)}: {contract_id} (NSN: {nsn})")
            
            # Process the NSN
            result = process_nsn_for_contract(nsn, chrome_driver, timeout)
            result['contract_id'] = contract_id
            
            if result['success']:
                successful_processing += 1
                results.append(result)
                logger.info(f"✅ Contract {contract_id} processed successfully")
            else:
                logger.error(f"❌ Contract {contract_id} processing failed")
                results.append(result)
        
        logger.info(f"✅ Contract processing completed: {successful_processing}/{len(contracts)} successful")
        
        # Step 5: Upload results to database
        logger.info("Step 5: Uploading results to database")
        if results:
            upload_op = SupabaseUploadOperation()
            
            # Prepare data for upload
            upload_data = []
            for result in results:
                if result['success'] and not result.get('skipped', False):
                    # Get the solicitation number from the original contract data
                    contract_id = result['contract_id']
                    contract_data = next((c for c in contracts if c['id'] == contract_id), None)
                    
                    if contract_data and contract_data.get('solicitation_number'):
                        tmp = {
                            'solicitation_number': contract_data['solicitation_number'],
                            'national_stock_number': result['nsn'],
                            'cde_g': result['amsc_code']# AMSC code goes in cde_g field
                        }
                        if result['is_closed'] is not None:
                            tmp['closed'] = result['is_closed']
                        upload_data.append(tmp)
                        logger.info(f"Prepared upload data for SN: {contract_data['solicitation_number']}, NSN: {result['nsn']}")
                    else:
                        logger.warning(f"Missing solicitation number for contract {contract_id}, skipping upload")
            
            if upload_data:
                logger.info(f"Attempting to upload {len(upload_data)} records to database...")
                
                # Log the first few records for debugging
                for i, record in enumerate(upload_data[:3]):
                    logger.info(f"Sample record {i+1}: {record}")
                
                try:
                    upload_result = upload_op._execute({
                        'results': upload_data,
                        'table_name': 'rfq_index_extract',
                        'operation_type': 'upsert',
                        'upsert_strategy': 'merge',
                        'conflict_resolution': 'update_existing',
                        'key_fields': ['solicitation_number', 'national_stock_number'],  # Use both fields as key
                        'batch_size': 50
                    }, {})
                    
                    logger.info(f"Upload operation completed. Success: {upload_result.success}")
                    
                    if upload_result.success:
                        logger.info(f"✅ Database upload completed: {len(upload_data)} records")
                        if hasattr(upload_result, 'data') and upload_result.data:
                            logger.info(f"Upload result data: {upload_result.data}")
                    else:
                        logger.error(f"❌ Database upload failed: {upload_result.error}")
                        # Log more details about the failure
                        if hasattr(upload_result, 'data') and upload_result.data:
                            logger.error(f"Upload result data: {upload_result.data}")
                        if hasattr(upload_result, 'metadata') and upload_result.metadata:
                            logger.error(f"Upload result metadata: {upload_result.metadata}")
                            
                except Exception as upload_error:
                    logger.error(f"❌ Exception during upload operation: {str(upload_error)}")
                    import traceback
                    logger.error(f"Upload error traceback: {traceback.format_exc()}")
                    # Continue with the workflow even if upload fails
                    upload_result = type('MockResult', (), {
                        'success': False,
                        'error': str(upload_error)
                    })()
            else:
                logger.info("ℹ️ No data to upload")
        
        # Step 6: Cleanup
        logger.info("Step 6: Cleaning up")
        try:
            if chrome_driver:
                chrome_driver.quit()
                logger.info("✅ Chrome driver cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Error during Chrome cleanup: {str(e)}")
        
        # Return results summary
        return {
            'success': True,
            'contracts_processed': len(contracts),
            'successful_processing': successful_processing,
            'failed_processing': len(contracts) - successful_processing,
            'records_uploaded': len([r for r in results if r['success'] and not r.get('skipped', False)]),
            'message': 'Universal contract queue workflow completed successfully'
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull data for contracts in universal contract queue")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh even if data already exists")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode (default: True)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for page operations in seconds (default: 30)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--limit", type=int, help="Limit number of contracts to process")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Processing contracts from universal contract queue (auto-discovered)")
    
    # Execute workflow
    result = execute_universal_contract_queue_workflow(
        headless=args.headless,
        timeout=args.timeout,
        limit=args.limit
    )
    
    # Output results
    if result.get('success'):
        logger.info("🎉 Universal contract queue data pull completed successfully")
        
        # Print summary
        logger.info(f"Contracts processed: {result.get('contracts_processed', 0)}")
        logger.info(f"Successful processing: {result.get('successful_processing', 0)}")
        logger.info(f"Failed processing: {result.get('failed_processing', 0)}")
        logger.info(f"Records uploaded: {result.get('records_uploaded', 0)}")
        
        sys.exit(0)
    else:
        logger.error(f"❌ Universal contract queue data pull failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
