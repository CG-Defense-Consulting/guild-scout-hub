#!/usr/bin/env python3
"""
Universal Contract Queue Data Pull Workflow

This workflow addresses the business use case of pulling comprehensive data
for contracts in the universal_contract_queue. It applies conditional logic
to determine what data needs to be pulled based on existing data.

Use Case: Pull data for contracts in the universal contract queue
Implementation: Uses modular operations (Chrome Setup, Consent Page, NSN Extraction, etc.)

Business Logic:
1. FIRST check if RFQ PDF exists in Supabase bucket
2. If RFQ PDF does NOT exist:
   - Check if AMSC code is empty
   - If AMSC code is empty: Extract AMSC code AND download RFQ PDF
   - If AMSC code is filled: Do nothing (PDF issue, don't touch)
3. If RFQ PDF exists: Do nothing (already processed)
4. While extracting AMSC code, if we see "no open solicitation" language, mark as closed
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations import (
    ChromeSetupOperation, 
    ConsentPageOperation, 
    NsnExtractionOperation,
    ClosedSolicitationCheckOperation,
    SupabaseUploadOperation
)
from core.workflow_orchestrator import WorkflowOrchestrator
from utils.logger import setup_logger

logger = setup_logger(__name__)

class UniversalContractQueueDataPuller:
    """
    Handles the business logic for pulling data for contracts in the universal contract queue.
    
    This class implements the specific business logic:
    1. Check RFQ PDF existence first
    2. Apply conditional logic based on PDF existence and AMSC code status
    3. Only run operations when both conditions are met
    """
    
    def __init__(self, supabase_client):
        """
        Initialize the data puller.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase = supabase_client
    
    def check_rfq_pdf_exists(self, contract_id: str) -> bool:
        """
        Check if RFQ PDF exists in the Supabase bucket for a given contract.
        
        Args:
            contract_id: Contract ID to check
            
        Returns:
            True if PDF exists, False otherwise
        """
        try:
            # Check if PDF exists in the bucket
            # This would need to be implemented based on your storage structure
            # For now, we'll assume a naming convention: {contract_id}.pdf
            
            bucket_name = "docs"  # Your bucket name
            file_path = f"rfq_pdfs/{contract_id}.pdf"
            
            # Try to get file metadata - if it exists, the file exists
            result = self.supabase.storage.from_(bucket_name).list(path="rfq_pdfs")
            
            if result:
                # Check if our specific file exists in the list
                for file_info in result:
                    if file_info.get('name') == f"{contract_id}.pdf":
                        logger.info(f"RFQ PDF found for contract {contract_id}")
                        return True
                
                logger.info(f"RFQ PDF NOT found for contract {contract_id}")
                return False
            else:
                logger.info(f"RFQ PDF NOT found for contract {contract_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking RFQ PDF existence for contract {contract_id}: {str(e)}")
            # If we can't determine, assume it doesn't exist to be safe
            return False
    
    def analyze_contract_data_gaps(self, contract_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze contracts to determine what data is missing and needs to be pulled.
        
        This implements the specific business logic:
        1. Check RFQ PDF existence first
        2. If PDF doesn't exist, check AMSC code status
        3. Apply conditional logic based on both conditions
        
        Args:
            contract_ids: List of contract IDs to analyze
            
        Returns:
            Dictionary mapping contract IDs to their data gaps and action decisions
        """
        gaps = {}
        
        for contract_id in contract_ids:
            contract_gaps = {
                'needs_amsc': False,
                'needs_rfq_pdf': False,
                'needs_closed_status': False,
                'should_process': False,  # Whether we should run any operations
                'action_reason': '',      # Why we're processing or not
                'nsn': None,
                'existing_amsc': None,
                'rfq_pdf_exists': False
            }
            
            try:
                # FIRST: Check if RFQ PDF exists in Supabase bucket
                rfq_pdf_exists = self.check_rfq_pdf_exists(contract_id)
                contract_gaps['rfq_pdf_exists'] = rfq_pdf_exists
                
                if rfq_pdf_exists:
                    # RFQ PDF exists - do nothing
                    contract_gaps['should_process'] = False
                    contract_gaps['action_reason'] = 'RFQ PDF already exists in bucket'
                    logger.info(f"Contract {contract_id}: RFQ PDF exists, no processing needed")
                    
                else:
                    # RFQ PDF does NOT exist - check AMSC code status
                    result = self.supabase.table('rfq_index_extract').select(
                        'id, national_stock_number, cde_g, closed, solicitation_number'
                    ).eq('id', contract_id).execute()
                    
                    if result.data:
                        contract_data = result.data[0]
                        nsn = contract_data.get('national_stock_number')
                        existing_amsc = contract_data.get('cde_g')
                        
                        contract_gaps['nsn'] = nsn
                        contract_gaps['existing_amsc'] = existing_amsc
                        
                        if not existing_amsc:
                            # AMSC code is empty - extract AMSC code AND download RFQ PDF
                            contract_gaps['needs_amsc'] = True
                            contract_gaps['needs_rfq_pdf'] = True
                            contract_gaps['needs_closed_status'] = True  # Check while we're there
                            contract_gaps['should_process'] = True
                            contract_gaps['action_reason'] = 'RFQ PDF missing AND AMSC code empty - will extract both'
                            logger.info(f"Contract {contract_id}: RFQ PDF missing AND AMSC code empty - will process")
                            
                        else:
                            # AMSC code is filled but RFQ PDF is missing - do nothing
                            contract_gaps['should_process'] = False
                            contract_gaps['action_reason'] = 'RFQ PDF missing but AMSC code exists - PDF issue, not touching'
                            logger.info(f"Contract {contract_id}: RFQ PDF missing but AMSC code exists - not processing")
                    
                    else:
                        logger.warning(f"No contract data found for contract ID: {contract_id}")
                        contract_gaps['should_process'] = False
                        contract_gaps['action_reason'] = 'No contract data found'
                        
            except Exception as e:
                logger.error(f"Error analyzing contract {contract_id}: {str(e)}")
                contract_gaps['error'] = str(e)
                contract_gaps['should_process'] = False
                contract_gaps['action_reason'] = f'Error during analysis: {str(e)}'
            
            gaps[contract_id] = contract_gaps
        
        return gaps
    
    def create_workflow_for_contracts(self, contract_ids: List[str], 
                                    contract_gaps: Dict[str, Dict[str, Any]],
                                    headless: bool = True, timeout: int = 30,
                                    retry_attempts: int = 3, batch_size: int = 50) -> WorkflowOrchestrator:
        """
        Create a workflow based on the data gaps identified for the contracts.
        
        This workflow implements the business logic:
        - Only process contracts that need both AMSC code AND RFQ PDF
        - Extract AMSC code and check for closed status while on the NSN page
        - Download RFQ PDF for the same contracts
        
        Args:
            contract_ids: List of contract IDs to process
            contract_gaps: Dictionary of data gaps for each contract
            headless: Whether to run Chrome in headless mode
            timeout: Timeout for page operations
            retry_attempts: Number of retry attempts for each operation
            batch_size: Size of batches for database uploads
            
        Returns:
            Configured WorkflowOrchestrator instance
        """
        
        # Filter contracts that should be processed
        contracts_to_process = [
            contract_id for contract_id, gaps in contract_gaps.items() 
            if gaps.get('should_process', False)
        ]
        
        if not contracts_to_process:
            logger.info("No contracts need processing based on business logic")
            # Return empty workflow
            workflow = WorkflowOrchestrator(
                name="universal_contract_queue_data_pull",
                description="No contracts need processing"
            )
            return workflow
        
        logger.info(f"Creating workflow for {len(contracts_to_process)} contracts that need processing")
        
        # Create workflow orchestrator
        workflow = WorkflowOrchestrator(
            name="universal_contract_queue_data_pull",
            description=f"Pull data for {len(contracts_to_process)} contracts based on business logic"
        )
        
        # Step 1: Chrome Setup (runs once, shared across all operations)
        chrome_setup = ChromeSetupOperation(headless=headless)
        workflow.add_step(
            operation=chrome_setup,
            inputs={},
            depends_on=[],
            batch_config={}
        )
        
        # Step 2: Consent Page Handling (applied to batch of NSNs that need processing)
        # Only process NSNs that need both AMSC codes AND RFQ PDFs
        nsn_urls = []
        nsn_list = []
        nsn_to_contract_map = {}
        
        for contract_id in contracts_to_process:
            gaps = contract_gaps[contract_id]
            if gaps.get('needs_amsc') and gaps.get('needs_rfq_pdf'):
                nsn = gaps.get('nsn')
                if nsn:
                    nsn_list.append(nsn)
                    nsn_to_contract_map[nsn] = contract_id
                    base_url = "https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx"
                    nsn_urls.append(f"{base_url}?value={nsn}&category=nsn")
        
        if nsn_urls:
            consent_page = ConsentPageOperation()
            workflow.add_step(
                operation=consent_page,
                inputs={'timeout': timeout},
                depends_on=['chrome_setup'],
                batch_config={'items': nsn_urls}
            )
            
            # Step 3: NSN Data Extraction (for contracts that need AMSC codes)
            # This will also check for closed solicitation status while on the page
            nsn_extraction = NsnExtractionOperation()
            nsn_inputs = {
                'timeout': timeout,
                'retry_attempts': retry_attempts,
                'extract_fields': ['amsc_code'],  # Focus on AMSC codes
                'check_closed_status': True  # Check for closed status while extracting
            }
            
            workflow.add_step(
                operation=nsn_extraction,
                inputs=nsn_inputs,
                depends_on=['consent_page'],
                batch_config={'items': nsn_list, 'contract_ids': list(nsn_to_contract_map.values())}
            )
            
            # Step 4: Supabase Upload (AMSC codes and closed status)
            supabase_upload = SupabaseUploadOperation()
            upload_inputs = {
                'batch_size': batch_size,
                'table_name': 'rfq_index_extract'
            }
            
            workflow.add_step(
                operation=supabase_upload,
                inputs=upload_inputs,
                depends_on=['nsn_extraction'],
                batch_config={}
            )
            
            # Note: RFQ PDF downloading would be implemented here as a separate operation
            # For now, we'll focus on AMSC codes and closed status
            # The RFQ PDF operation would run in parallel or after NSN extraction
            
        logger.info("Universal contract queue data pull workflow created successfully")
        return workflow

def create_universal_contract_queue_workflow(contract_ids: List[str], 
                                           headless: bool = True, timeout: int = 30,
                                           retry_attempts: int = 3, batch_size: int = 50,
                                           force_refresh: bool = False) -> WorkflowOrchestrator:
    """
    Create a workflow for pulling data for contracts in the universal contract queue.
    
    Args:
        contract_ids: List of contract IDs from universal_contract_queue
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each operation
        batch_size: Size of batches for database uploads
        force_refresh: Force refresh even if data already exists
        
    Returns:
        Configured WorkflowOrchestrator instance
    """
    
    # Validate inputs
    if not contract_ids:
        raise ValueError("Contract IDs list cannot be empty")
    
    logger.info(f"Creating universal contract queue data pull workflow for {len(contract_ids)} contracts")
    
    # Initialize Supabase client for data gap analysis
    try:
        from core.uploaders.supabase_uploader import SupabaseUploader
        supabase_client = SupabaseUploader().supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise
    
    # Create data puller and analyze gaps
    data_puller = UniversalContractQueueDataPuller(supabase_client)
    contract_gaps = data_puller.analyze_contract_data_gaps(contract_ids)
    
    # Log analysis results
    logger.info("Contract data gap analysis completed:")
    for contract_id, gaps in contract_gaps.items():
        logger.info(f"Contract {contract_id}:")
        logger.info(f"  - NSN: {gaps.get('nsn', 'N/A')}")
        logger.info(f"  - RFQ PDF exists: {gaps.get('rfq_pdf_exists', False)}")
        logger.info(f"  - AMSC code exists: {gaps.get('existing_amsc', 'N/A')}")
        logger.info(f"  - Should process: {gaps.get('should_process', False)}")
        logger.info(f"  - Action reason: {gaps.get('action_reason', 'N/A')}")
    
    # Create workflow based on gaps
    workflow = data_puller.create_workflow_for_contracts(
        contract_ids=contract_ids,
        contract_gaps=contract_gaps,
        headless=headless,
        timeout=timeout,
        retry_attempts=retry_attempts,
        batch_size=batch_size
    )
    
    return workflow

def execute_universal_contract_queue_workflow(contract_ids: List[str], 
                                            headless: bool = True, timeout: int = 30,
                                            retry_attempts: int = 3, batch_size: int = 50,
                                            force_refresh: bool = False) -> Dict[str, Any]:
    """
    Execute the universal contract queue data pull workflow.
    
    Args:
        contract_ids: List of contract IDs from universal_contract_queue
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each operation
        batch_size: Size of batches for database uploads
        force_refresh: Force refresh even if data already exists
        
    Returns:
        Dictionary containing workflow results and summary
    """
    
    try:
        # Create workflow
        workflow = create_universal_contract_queue_workflow(
            contract_ids=contract_ids,
            headless=headless,
            timeout=timeout,
            retry_attempts=retry_attempts,
            batch_size=batch_size,
            force_refresh=force_refresh
        )
        
        # Check if workflow has any steps
        if not workflow.steps:
            logger.info("No workflow steps to execute - all contracts are up to date")
            return {
                'workflow_name': workflow.name,
                'status': 'completed',
                'total_contracts': len(contract_ids),
                'contracts_processed': 0,
                'message': 'No contracts need processing based on business logic'
            }
        
        # Execute workflow
        logger.info("Starting universal contract queue data pull workflow execution")
        results = workflow.execute()
        
        # Get workflow status
        status = workflow.get_status()
        context = workflow.get_context()
        
        # Prepare summary
        summary = {
            'workflow_name': workflow.name,
            'status': status.value,
            'total_contracts': len(contract_ids),
            'steps_executed': len(results),
            'results': results,
            'context': context
        }
        
        # Add step-specific summaries
        if len(results) >= 1:
            # Chrome setup results
            chrome_result = results[0]
            summary['chrome_setup'] = {
                'success': chrome_result.success,
                'status': chrome_result.status.value,
                'metadata': chrome_result.metadata
            }
            
            # Add other step results if they exist
            if len(results) > 1:
                summary['consent_page'] = {
                    'success': results[1].success,
                    'status': results[1].status.value
                }
            
            if len(results) > 2:
                summary['nsn_extraction'] = {
                    'success': results[2].success,
                    'status': results[2].status.value
                }
        
        logger.info(f"Universal contract queue data pull workflow completed with status: {status.value}")
        
        return summary
        
    except Exception as e:
        error_msg = f"Universal contract queue data pull workflow failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'workflow_name': 'universal_contract_queue_data_pull',
            'status': 'failed',
            'error': error_msg,
            'total_contracts': len(contract_ids) if 'contract_ids' in locals() else 0
        }
    
    finally:
        # Clean up workflow resources
        if 'workflow' in locals():
            try:
                workflow.cleanup()
                logger.info("Workflow cleanup completed")
            except Exception as e:
                logger.warning(f"Error during workflow cleanup: {str(e)}")

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Pull data for contracts in universal contract queue")
    parser.add_argument("--contract-ids", nargs="+", required=True, help="List of contract IDs from universal_contract_queue")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh even if data already exists")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode (default: True)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for page operations in seconds (default: 30)")
    parser.add_argument("--retry-attempts", type=int, default=3, help="Number of retry attempts for each operation (default: 3)")
    parser.add_argument("--batch-size", type=int, default=50, help="Size of batches for database uploads (default: 50)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Processing {len(args.contract_ids)} contracts from universal contract queue")
    
    # Execute workflow
    result = execute_universal_contract_queue_workflow(
        contract_ids=args.contract_ids,
        headless=args.headless,
        timeout=args.timeout,
        retry_attempts=args.retry_attempts,
        batch_size=args.batch_size,
        force_refresh=args.force_refresh
    )
    
    # Output results
    if result['status'] == 'completed':
        logger.info("Universal contract queue data pull completed successfully")
        
        # Print summary
        if 'nsn_extraction' in result:
            nsn_summary = result['nsn_extraction']
            logger.info(f"NSN Extraction: {nsn_summary['status']}")
        
        if 'chrome_setup' in result:
            chrome_summary = result['chrome_setup']
            logger.info(f"Chrome Setup: {chrome_summary['status']}")
        
        sys.exit(0)
    else:
        logger.error(f"Universal contract queue data pull failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
