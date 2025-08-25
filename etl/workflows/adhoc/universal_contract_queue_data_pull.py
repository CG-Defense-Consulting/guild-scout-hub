#!/usr/bin/env python3
"""
Universal Contract Queue Data Pull Workflow

This workflow addresses the business use case of pulling comprehensive data
for contracts in the universal_contract_queue. It applies conditional logic
to determine what data needs to be pulled based on existing data.

Use Case: Pull data for contracts in the universal contract queue
Implementation: Uses modular operations (Chrome Setup, Consent Page, NSN Extraction, etc.)

Business Logic:
1. INTERNALLY query universal_contract_queue for contracts with missing data
2. Apply predefined conditions to filter contracts that need processing
3. If AMSC code is missing: Extract AMSC code
4. If RFQ PDF is missing: Download RFQ PDF  
5. While extracting AMSC code, if we see "no open solicitation" language, mark as closed
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations import (
    BaseOperation, 
    ChromeSetupOperation, 
    ConsentPageOperation, 
    AmscExtractionOperation,
    ClosedSolicitationCheckOperation,
    NsnPageNavigationOperation,
    SupabaseUploadOperation
)

from utils.logger import setup_logger

logger = setup_logger(__name__)

class UniversalContractQueueDataPuller:
    """
    Handles the business logic for pulling data for contracts in the universal contract queue.
    
    This class:
    1. INTERNALLY queries universal_contract_queue to find contracts with missing data
    2. Applies predefined filtering conditions to determine what needs to be pulled
    3. Orchestrates the appropriate operations based on data gaps
    """
    
    def __init__(self, supabase_client):
        """
        Initialize the data puller.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
    
    def query_contracts_needing_processing(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Single query to find contracts needing AMSC codes using proper JOIN.
        
        Args:
            limit: Optional limit on number of contracts to process
            
        Returns:
            List of contract data that needs processing
        """
        try:
            logger.info("Querying contracts needing AMSC codes...")
            
            # Debug: First check what data exists
            logger.info("DEBUG: Checking raw data in tables...")
            
            # Check universal_contract_queue
            ucq_debug = self.supabase.table('universal_contract_queue').select('id').limit(1).execute()
            logger.info(f"DEBUG: UCQ sample: {ucq_debug.data}")
            
            # Check rfq_index_extract
            rie_debug = self.supabase.table('rfq_index_extract').select('id,cde_g,solicitation_number,national_stock_number').limit(1).execute()
            logger.info(f"DEBUG: RIE sample: {rie_debug.data}")
            
            # Single JOIN query to get contracts with missing AMSC codes
            # Using proper Supabase syntax with table() and inner join
            result = self.supabase.table('universal_contract_queue').select(
                "id,rfq_index_extract!inner(cde_g,solicitation_number,national_stock_number)"
            ).execute()
            
            if not result.data:
                logger.info("No contracts found in universal_contract_queue")
                return []
            
            # Transform the nested result structure and filter for missing AMSC codes
            contracts_needing_processing = []
            for contract in result.data:
                contract_id = contract['id']
                rie_data = contract['rfq_index_extract']
                cde_g = rie_data.get('cde_g')
                
                # Check if AMSC code is missing (None, empty string, or whitespace)
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
    
    def check_rfq_pdf_exists(self, solicitation_number: str) -> bool:
        """
        Check if RFQ PDF exists in the Supabase bucket using solicitation number.
        
        Args:
            solicitation_number: Solicitation number to check
            
        Returns:
            True if PDF exists, False otherwise
        """
        try:
            bucket_name = "docs"
            
            # Try to get file metadata - if it exists, the file exists
            result = self.supabase.storage.from_(bucket_name).list()
            
            if result:
                # Check if our specific file exists in the list
                for file_info in result:
                    if file_info.get('name').endswith(f"{solicitation_number}.pdf"):
                        logger.info(f"RFQ PDF found for solicitation {solicitation_number}")
                        return True
                
                logger.info(f"RFQ PDF NOT found for solicitation {solicitation_number}")
                return False
            else:
                logger.info(f"RFQ PDF NOT found for solicitation {solicitation_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking RFQ PDF existence for solicitation {solicitation_number}: {str(e)}")
            # If we can't determine, assume it doesn't exist to be safe
            return False
    
    def analyze_contract_data_gaps(self, contracts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze contracts to determine what data is missing and needs to be pulled.
        
        Args:
            contracts: List of contracts from universal_contract_queue
            
        Returns:
            Dictionary mapping contract IDs to their data gaps and action decisions
        """
        gaps = {}
        
        for contract in contracts:
            contract_id = contract['id']
            solicitation_number = contract.get('solicitation_number')
            nsn = contract.get('national_stock_number')
            
            contract_gaps = {
                'needs_amsc': True,  # Always need AMSC code if we're here
                'needs_rfq_pdf': False,
                'should_process': True,
                'action_reason': '',
                'nsn': nsn,
                'solicitation_number': solicitation_number,
                'rfq_pdf_exists': False,
                'contract_data': contract
            }
            
            try:
                # Check if RFQ PDF exists using solicitation number
                rfq_pdf_exists = self.check_rfq_pdf_exists(solicitation_number)
                contract_gaps['rfq_pdf_exists'] = rfq_pdf_exists
                
                if rfq_pdf_exists:
                    # PDF exists, only need AMSC code
                    contract_gaps['needs_rfq_pdf'] = False
                    contract_gaps['action_reason'] = 'RFQ PDF exists, only need AMSC code'
                    logger.info(f"Contract {contract_id}: RFQ PDF exists, only need AMSC code")
                else:
                    # PDF missing, need both AMSC code and RFQ PDF
                    contract_gaps['needs_rfq_pdf'] = True
                    contract_gaps['action_reason'] = 'RFQ PDF missing, need both AMSC code and RFQ PDF'
                    logger.info(f"Contract {contract_id}: RFQ PDF missing, need both AMSC code and RFQ PDF")
                        
            except Exception as e:
                logger.error(f"Error analyzing contract {contract_id}: {str(e)}")
                contract_gaps['error'] = str(e)
                contract_gaps['should_process'] = False
                contract_gaps['action_reason'] = f'Error during analysis: {str(e)}'
            
            gaps[contract_id] = contract_gaps
        
        return gaps
    


    def execute_with_data_flow(self, headless: bool = True, timeout: int = 30,
                              retry_attempts: int = 3, batch_size: int = 50,
                              force_refresh: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute the universal contract queue workflow with proper data flow between operations.
        
        This method orchestrates the execution by:
        1. Running Chrome setup once
        2. Handling consent pages for all NSNs
        3. Navigating to each NSN page and collecting HTML content
        4. Processing the HTML content for closed status and AMSC extraction
        5. Uploading results to Supabase
        
        Args:
            headless: Whether to run Chrome in headless mode
            timeout: Timeout for page operations
            retry_attempts: Number of retry attempts for each operation
            batch_size: Size of batches for database uploads
            force_refresh: Force refresh even if data already exists
            limit: Optional limit on number of contracts to process
            
        Returns:
            Dictionary containing workflow results and summary
        """
        try:
            logger.info("🚀 WORKFLOW: Starting universal contract queue data pull with data flow orchestration")
            
            # Step 1: Create and execute Chrome setup
            chrome_setup = ChromeSetupOperation(headless=headless)
            chrome_result = chrome_setup.execute({}, {})
            
            if not chrome_result.success:
                logger.error(f"❌ WORKFLOW: Chrome setup failed: {chrome_result.error}")
                return {
                    'success': False,
                    'status': 'failed',
                    'error': f"Chrome setup failed: {chrome_result.error}"
                }
            
            chrome_driver = chrome_result.data.get('driver')
            logger.info("✅ WORKFLOW: Chrome setup completed successfully")
            
            # Step 2: Query contracts needing processing
            contracts = self.query_contracts_needing_processing(limit=limit)
            
            if not contracts:
                logger.info("ℹ️ WORKFLOW: No contracts need processing")
                return {
                    'success': True,
                    'status': 'completed',
                    'contracts_processed': 0,
                    'message': 'No contracts need processing'
                }
            
            # Step 3: Analyze data gaps
            contract_gaps = self.analyze_contract_data_gaps(contracts)
            contracts_to_process = [
                contract_id for contract_id, gaps in contract_gaps.items() 
                if gaps.get('should_process', False)
            ]
            
            if not contracts_to_process:
                logger.info("ℹ️ WORKFLOW: No contracts need processing based on gaps")
                return {
                    'success': True,
                    'status': 'completed',
                    'contracts_processed': 0,
                    'message': 'No contracts need processing based on gaps'
                }
            
            logger.info(f"🚀 WORKFLOW: Processing {len(contracts_to_process)} contracts")
            
            # Step 4: Build NSN list
            nsn_list = []
            for contract_id in contracts_to_process:
                gaps = contract_gaps[contract_id]
                nsn = gaps.get('nsn')
                if nsn:
                    nsn_list.append(nsn)
            
            if not nsn_list:
                logger.info("ℹ️ WORKFLOW: No NSNs found for processing")
                return {
                    'success': True,
                    'status': 'completed',
                    'contracts_processed': 0,
                    'message': 'No NSNs found for processing'
                }
            
            logger.info(f"🚀 WORKFLOW: Processing {len(nsn_list)} NSNs: {nsn_list}")
            
            # Step 5: Process each NSN individually through the complete flow
            # ChromeDriver operates on state, so we must process each NSN completely before moving to the next
            closed_status_results = []
            amsc_extraction_results = []
            rfq_pdf_results = []
            
            for i, nsn in enumerate(nsn_list):
                logger.info(f"🚀 WORKFLOW: Processing NSN {i+1}/{len(nsn_list)}: {nsn}")
                
                try:
                    # Step 5a: Navigate to NSN page
                    nsn_navigation = NsnPageNavigationOperation()
                    nav_result = nsn_navigation.execute(
                        inputs={'nsn': nsn, 'chrome_driver': chrome_driver, 'timeout': timeout, 'retry_attempts': retry_attempts},
                        context={'chrome_driver': chrome_driver}
                    )
                    
                    if not nav_result.success:
                        logger.error(f"❌ WORKFLOW: Navigation failed for NSN {nsn}: {nav_result.error}")
                        continue
                    
                    logger.info(f"✅ WORKFLOW: Successfully navigated to NSN {nsn}")
                    
                    # Step 5b: Handle consent page (if present)
                    consent_page = ConsentPageOperation()
                    consent_result = consent_page.execute(
                        inputs={'nsn': nsn, 'timeout': timeout, 'retry_attempts': retry_attempts},
                        context={'chrome_driver': chrome_driver}
                    )
                    
                    if consent_result.success:
                        logger.info(f"✅ WORKFLOW: Consent page handled for NSN {nsn}")
                    else:
                        logger.warning(f"⚠️ WORKFLOW: Consent page handling failed for NSN {nsn}: {consent_result.error}")
                    
                    # Step 5c: Get the current page HTML content after consent handling
                    html_content = chrome_driver.page_source
                    logger.info(f"🔍 WORKFLOW: Retrieved HTML content for NSN {nsn} (length: {len(html_content)} characters)")
                    
                    # Step 5d: Check if solicitation is closed
                    closed_check = ClosedSolicitationCheckOperation()
                    closed_result = closed_check.execute(
                        inputs={'html_content': html_content, 'nsn': nsn},
                        context={}
                    )
                    closed_status_results.append(closed_result)
                    
                    if closed_result.success:
                        is_closed = closed_result.data.get('is_closed')
                        logger.info(f"🔍 WORKFLOW: NSN {nsn} closed status: {is_closed}")
                        
                        # If closed, skip AMSC extraction and RFQ PDF download
                        if is_closed:
                            logger.info(f"ℹ️ WORKFLOW: NSN {nsn} is closed, skipping AMSC extraction and RFQ PDF download")
                            amsc_extraction_results.append(None)
                            rfq_pdf_results.append(None)
                            continue
                    
                    # Step 5e: Extract AMSC code (only if not closed)
                    amsc_extraction = AmscExtractionOperation()
                    amsc_result = amsc_extraction.execute(
                        inputs={'html_content': html_content, 'nsn': nsn},
                        context={}
                    )
                    amsc_extraction_results.append(amsc_result)
                    
                    if amsc_result.success:
                        amsc_code = amsc_result.data.get('amsc_code')
                        logger.info(f"🔍 WORKFLOW: NSN {nsn} AMSC code: {amsc_code}")
                    else:
                        logger.warning(f"⚠️ WORKFLOW: AMSC extraction failed for NSN {nsn}: {amsc_result.error}")
                    
                    # Step 5f: Download RFQ PDF if applicable
                    # Check if this contract needs RFQ PDF
                    contract_id = contracts_to_process[i] if i < len(contracts_to_process) else None
                    if contract_id and contract_gaps.get(contract_id, {}).get('needs_rfq_pdf', False):
                        logger.info(f"📄 WORKFLOW: NSN {nsn} needs RFQ PDF download")
                        # Here you would add RFQ PDF download logic
                        # For now, we'll just log it
                        rfq_pdf_results.append("needs_download")
                    else:
                        rfq_pdf_results.append(None)
                    
                    logger.info(f"✅ WORKFLOW: Completed processing NSN {nsn}")
                    
                except Exception as e:
                    logger.error(f"❌ WORKFLOW: Error processing NSN {nsn}: {str(e)}")
                    # Add None results for failed processing
                    closed_status_results.append(None)
                    amsc_extraction_results.append(None)
                    rfq_pdf_results.append(None)
            
            logger.info(f"✅ WORKFLOW: NSN processing completed. {len(closed_status_results)}/{len(nsn_list)} NSNs processed")
            
            # Step 8: Upload results to Supabase
            supabase_upload = SupabaseUploadOperation()
            
            # Prepare data for upload
            upload_data = []
            for i, contract_id in enumerate(contracts_to_process):
                if i < len(amsc_extraction_results) and i < len(closed_status_results):
                    amsc_result = amsc_extraction_results[i]
                    closed_result = closed_status_results[i]
                    
                    if amsc_result.success and closed_result.success:
                        upload_data.append({
                            'contract_id': contract_id,
                            'nsn': nsn_list[i] if i < len(nsn_list) else None,
                            'amsc_code': amsc_result.data.get('amsc_code'),
                            'is_closed': closed_result.data.get('is_closed'),
                            'processed_at': 'now()'
                        })
            
            if upload_data:
                upload_result = supabase_upload.execute(
                    inputs={'results': upload_data, 'batch_size': batch_size, 'table_name': 'rfq_index_extract'},
                    context={}
                )
                
                if upload_result.success:
                    logger.info(f"✅ WORKFLOW: Supabase upload completed. {len(upload_data)} records uploaded")
                else:
                    logger.error(f"❌ WORKFLOW: Supabase upload failed: {upload_result.error}")
            else:
                logger.warning("⚠️ WORKFLOW: No data to upload")
            
            # Step 9: Cleanup
            try:
                if chrome_driver:
                    chrome_driver.quit()
                    logger.info("🧹 WORKFLOW: Chrome driver cleaned up")
            except Exception as e:
                logger.warning(f"⚠️ WORKFLOW: Error during Chrome cleanup: {str(e)}")
            
            # Return results summary
            successful_closed_checks = len([r for r in closed_status_results if r and r.success])
            successful_amsc_extractions = len([r for r in amsc_extraction_results if r and r.success])
            successful_rfq_pdfs = len([r for r in rfq_pdf_results if r == "needs_download"])
            
            return {
                'success': True,
                'status': 'completed',
                'contracts_processed': len(contracts_to_process),
                'nsns_processed': len(nsn_list),
                'closed_status_checks': successful_closed_checks,
                'amsc_extractions': successful_amsc_extractions,
                'rfq_pdfs_needed': successful_rfq_pdfs,
                'records_uploaded': len(upload_data) if 'upload_data' in locals() else 0,
                'message': 'Universal contract queue workflow completed successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ WORKFLOW: Universal contract queue workflow failed: {str(e)}")
            return {
                'success': False,
                'status': 'failed',
                'error': str(e)
            }



def execute_universal_contract_queue_workflow(headless: bool = True, timeout: int = 30,
                                            retry_attempts: int = 3, batch_size: int = 50,
                                            force_refresh: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Execute the universal contract queue data pull workflow.
    
    This workflow INTERNALLY determines which contracts need processing by
    querying the universal_contract_queue table.
    
    Args:
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each operation
        batch_size: Size of batches for database uploads
        force_refresh: Force refresh even if data already exists
        limit: Optional limit on number of contracts to process
        
    Returns:
        Dictionary containing workflow results and summary
    """
    
    try:
        # Initialize Supabase client for data gap analysis
        try:
            from core.uploaders.supabase_uploader import SupabaseUploader
            supabase_client = SupabaseUploader().supabase
            
            if not supabase_client:
                logger.error("Failed to initialize Supabase client - no client available")
                raise RuntimeError("Supabase client not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
        
        # Create data puller and execute with data flow orchestration
        data_puller = UniversalContractQueueDataPuller(supabase_client)
        
        logger.info("Starting universal contract queue data pull workflow with data flow orchestration")
        execution_result = data_puller.execute_with_data_flow(
            headless=headless,
            timeout=timeout,
            retry_attempts=retry_attempts,
            batch_size=batch_size,
            force_refresh=force_refresh,
            limit=limit
        )
        
        if execution_result.get('success'):
            logger.info("Universal contract queue data pull workflow completed successfully")
            logger.info(f"Contracts processed: {execution_result.get('contracts_processed', 0)}")
            logger.info(f"NSNs processed: {execution_result.get('nsns_processed', 0)}")
            logger.info(f"Records uploaded: {execution_result.get('records_uploaded', 0)}")
            
            return execution_result
        else:
            error_msg = execution_result.get('error', 'Unknown workflow error')
            logger.error(f"Universal contract queue data pull workflow failed: {error_msg}")
            return execution_result
        
    except Exception as e:
        error_msg = f"Universal contract queue data pull workflow failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'workflow_name': 'universal_contract_queue_data_pull',
            'status': 'failed',
            'error': error_msg
        }

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull data for contracts in universal contract queue")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh even if data already exists")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode (default: True)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for page operations in seconds (default: 30)")
    parser.add_argument("--retry-attempts", type=int, default=3, help="Number of retry attempts for each operation (default: 3)")
    parser.add_argument("--batch-size", type=int, default=50, help="Size of batches for database uploads (default: 50)")
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
        retry_attempts=args.retry_attempts,
        batch_size=args.batch_size,
        force_refresh=args.force_refresh,
        limit=args.limit
    )
    
    # Output results
    if result.get('success'):
        logger.info("Universal contract queue data pull completed successfully")
        
        # Print summary
        logger.info(f"Contracts processed: {result.get('contracts_processed', 0)}")
        logger.info(f"NSNs processed: {result.get('nsns_processed', 0)}")
        logger.info(f"Consent pages handled: {result.get('consent_successful', 0)}")
        logger.info(f"Navigation successful: {result.get('navigation_successful', 0)}")
        logger.info(f"Closed status checks: {result.get('closed_status_checks', 0)}")
        logger.info(f"AMSC extractions: {result.get('amsc_extractions', 0)}")
        logger.info(f"Records uploaded: {result.get('records_uploaded', 0)}")
        
        sys.exit(0)
    else:
        logger.error(f"Universal contract queue data pull failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
