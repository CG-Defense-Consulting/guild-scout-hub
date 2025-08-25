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
    NsnExtractionOperation,
    SupabaseUploadOperation
)
from core.workflow_orchestrator import WorkflowOrchestrator, WorkflowStatus
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
            ucq_debug = self.supabase.table('universal_contract_queue').select('id').limit(5).execute()
            logger.info(f"DEBUG: UCQ sample: {ucq_debug.data}")
            
            # Check rfq_index_extract
            rie_debug = self.supabase.table('rfq_index_extract').select('id,cde_g,solicitation_number,national_stock_number').limit(5).execute()
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
            file_path = f"rfq_pdfs/{solicitation_number}.pdf"
            
            # Try to get file metadata - if it exists, the file exists
            result = self.supabase.storage.from_(bucket_name).list(path="rfq_pdfs")
            
            if result:
                # Check if our specific file exists in the list
                for file_info in result:
                    if file_info.get('name') == f"{solicitation_number}.pdf":
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
    
    def create_workflow_for_contracts(self, contracts: List[Dict[str, Any]], 
                                    contract_gaps: Dict[str, Dict[str, Any]],
                                    headless: bool = True, timeout: int = 30,
                                    retry_attempts: int = 3, batch_size: int = 50) -> WorkflowOrchestrator:
        """
        Create a workflow for extracting AMSC codes and downloading RFQ PDFs.
        
        Args:
            contracts: List of contracts from universal_contract_queue
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
            logger.info("No contracts need processing")
            workflow = WorkflowOrchestrator(
                name="universal_contract_queue_data_pull",
                description="No contracts need processing"
            )
            return workflow
        
        logger.info(f"Creating workflow for {len(contracts_to_process)} contracts")
        
        # Create workflow orchestrator
        workflow = WorkflowOrchestrator(
            name="universal_contract_queue_data_pull",
            description=f"Extract AMSC codes and download RFQ PDFs for {len(contracts_to_process)} contracts"
        )
        
        # Step 1: Chrome Setup (runs once)
        chrome_setup = ChromeSetupOperation(headless=headless)
        workflow.add_step(
            operation=chrome_setup,
            inputs={},
            depends_on=[],
            batch_config={}
        )
        
        # Step 2: Handle consent pages for all NSNs
        if nsn_list:
            consent_page = ConsentPageOperation()
            workflow.add_step(
                operation=consent_page,
                inputs={'timeout': timeout, 'retry_attempts': retry_attempts},
                depends_on=['chrome_setup'],
                batch_config={'items': nsn_list}
            )
            
            # Step 3: Extract AMSC codes for all contracts (after consent)
            nsn_extraction = NsnExtractionOperation()
            workflow.add_step(
                operation=nsn_extraction,
                inputs={'timeout': timeout, 'retry_attempts': retry_attempts},
                depends_on=['consent_page'],  # Now depends on consent page, not chrome setup
                batch_config={'items': nsn_list}
            )
        
        # Step 4: Download RFQ PDFs for contracts that need them (after consent)
        contracts_needing_pdfs = [
            contract_id for contract_id in contracts_to_process
            if contract_gaps[contract_id].get('needs_rfq_pdf', False)
        ]
        
        if contracts_needing_pdfs:
            # Get solicitation numbers for PDF download
            solicitation_numbers = []
            for contract_id in contracts_needing_pdfs:
                gaps = contract_gaps[contract_id]
                solicitation_number = gaps.get('solicitation_number')
                if solicitation_number:
                    solicitation_numbers.append(solicitation_number)
            
            if solicitation_numbers:
                from core.operations import RfqPdfDownloadOperation
                rfq_pdf_download = RfqPdfDownloadOperation()
                workflow.add_step(
                    operation=rfq_pdf_download,
                    inputs={'timeout': timeout, 'retry_attempts': retry_attempts},
                    depends_on=['consent_page'],  # Now depends on consent page handling
                    batch_config={'items': solicitation_numbers}
                )
                logger.info(f"Added RFQ PDF download for {len(solicitation_numbers)} solicitations")
        
        # Step 5: Upload extracted data to Supabase
        if nsn_list:
            supabase_upload = SupabaseUploadOperation()
            workflow.add_step(
                operation=supabase_upload,
                inputs={'batch_size': batch_size, 'table_name': 'rfq_index_extract'},
                depends_on=['nsn_extraction'],
                batch_config={}
            )
        
        return workflow

def create_universal_contract_queue_workflow(headless: bool = True, timeout: int = 30,
                                           retry_attempts: int = 3, batch_size: int = 50,
                                           force_refresh: bool = False, limit: Optional[int] = None) -> WorkflowOrchestrator:
    """
    Create a workflow for pulling data for contracts in the universal contract queue.
    
    This workflow INTERNALLY queries the universal_contract_queue table to find
    contracts that need processing based on predefined conditions.
    
    Args:
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each operation
        batch_size: Size of batches for database uploads
        force_refresh: Force refresh even if data already exists
        limit: Optional limit on number of contracts to process
        
    Returns:
        Configured WorkflowOrchestrator instance
    """
    
    logger.info("Creating universal contract queue data pull workflow")
    
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
    
    # Create data puller and query contracts needing processing
    data_puller = UniversalContractQueueDataPuller(supabase_client)
    contracts = data_puller.query_contracts_needing_processing(limit=limit)
    
    if not contracts:
        logger.info("No contracts found in universal_contract_queue that need processing")
        # Return empty workflow
        workflow = WorkflowOrchestrator(
            name="universal_contract_queue_data_pull",
            description="No contracts need processing"
        )
        return workflow
    
    # Analyze data gaps for the found contracts
    contract_gaps = data_puller.analyze_contract_data_gaps(contracts)
    
    # Log analysis results
    logger.info("Contract data gap analysis completed:")
    for contract_id, gaps in contract_gaps.items():
        contract_data = gaps.get('contract_data', {})
        logger.info(f"Contract {contract_id} ({contract_data.get('solicitation_number', 'N/A')}):")
        logger.info(f"  - NSN: {gaps.get('nsn', 'N/A')}")
        logger.info(f"  - RFQ PDF exists: {gaps.get('rfq_pdf_exists', False)}")
        logger.info(f"  - AMSC code exists: {gaps.get('existing_amsc', 'N/A')}")
        logger.info(f"  - Should process: {gaps.get('should_process', False)}")
        logger.info(f"  - Action reason: {gaps.get('action_reason', 'N/A')}")
    
    # Create workflow based on gaps
    workflow = data_puller.create_workflow_for_contracts(
        contracts=contracts,
        contract_gaps=contract_gaps,
        headless=headless,
        timeout=timeout,
        retry_attempts=retry_attempts,
        batch_size=batch_size
    )
    
    return workflow

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
        # Create workflow
        workflow = create_universal_contract_queue_workflow(
            headless=headless,
            timeout=timeout,
            retry_attempts=retry_attempts,
            batch_size=batch_size,
            force_refresh=force_refresh,
            limit=limit
        )
        
        # Check if workflow has any steps
        if not workflow.steps:
            logger.info("No workflow steps to execute - all contracts are up to date")
            return {
                'workflow_name': workflow.name,
                'status': 'completed',
                'contracts_processed': 0,
                'message': 'No contracts need processing based on business logic'
            }
        
        # Execute the workflow
        logger.info("Starting universal contract queue data pull workflow execution")
        execution_result = workflow.execute()
        
        if execution_result['status'] == WorkflowStatus.COMPLETED:
            logger.info("Universal contract queue data pull workflow completed successfully")
            results = execution_result['results']
            logger.info(f"Workflow completed with {len(results)} step results")
            
            # Log step results
            for i, result in enumerate(results):
                logger.info(f"Step {i+1}: {result.status} - {result.metadata if result.metadata else 'No metadata'}")
            
            return {
                'success': True,
                'status': 'completed',
                'steps_executed': len(results),
                'results': results
            }
        else:
            error_msg = execution_result.get('error', 'Unknown workflow error')
            logger.error(f"Universal contract queue data pull workflow failed: {error_msg}")
            return {
                'success': False,
                'status': 'failed',
                'error': error_msg,
                'steps_executed': len(execution_result.get('results', []))
            }
        
    except Exception as e:
        error_msg = f"Universal contract queue data pull workflow failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'workflow_name': 'universal_contract_queue_data_pull',
            'status': 'failed',
            'error': error_msg
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
