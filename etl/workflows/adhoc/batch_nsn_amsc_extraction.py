#!/usr/bin/env python3
"""
Batch NSN AMSC Code Extraction Workflow

This workflow efficiently processes multiple NSNs by:
1. Setting up Chrome and ChromeDriver ONCE
2. Extracting AMSC codes for each NSN in the list
3. Uploading all results to Supabase in a single operation

This eliminates the overhead of spinning up environments for each individual NSN.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.operations import ChromeSetupOperation, AmscExtractionOperation, SupabaseUploadOperation
from core.workflow_orchestrator import WorkflowOrchestrator
from utils.logger import setup_logger

logger = setup_logger(__name__)

def create_batch_nsn_amsc_workflow(nsn_list: List[str], contract_ids: List[str] = None, 
                                  headless: bool = True, timeout: int = 30, 
                                  retry_attempts: int = 3, batch_size: int = 50) -> WorkflowOrchestrator:
    """
    Create a workflow for batch NSN AMSC extraction.
    
    Args:
        nsn_list: List of NSNs to process
        contract_ids: Optional list of contract IDs corresponding to NSNs
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each NSN
        batch_size: Size of batches for database uploads
        
    Returns:
        Configured WorkflowOrchestrator instance
    """
    
    # Validate inputs
    if not nsn_list:
        raise ValueError("NSN list cannot be empty")
    
    if contract_ids and len(contract_ids) != len(nsn_list):
        raise ValueError("Contract IDs list must match NSN list length")
    
    logger.info(f"Creating batch NSN AMSC extraction workflow for {len(nsn_list)} NSNs")
    
    # Create workflow orchestrator
    workflow = WorkflowOrchestrator(
        name="batch_nsn_amsc_extraction",
        description=f"Extract AMSC codes for {len(nsn_list)} NSNs using shared Chrome instance"
    )
    
    # Step 1: Chrome Setup (runs once)
    chrome_setup = ChromeSetupOperation(headless=headless)
    workflow.add_step(
        operation=chrome_setup,
        inputs={},
        depends_on=[],
        batch_config={}
    )
    
    # Step 2: AMSC Extraction (applied to batch of NSNs)
    amsc_extraction = AmscExtractionOperation()
    
    # Prepare inputs for AMSC extraction
    amsc_inputs = {
        'timeout': timeout,
        'retry_attempts': retry_attempts
    }
    
    # If contract IDs provided, add them to the batch config
    batch_config = {
        'items': nsn_list,
        'contract_ids': contract_ids if contract_ids else None
    }
    
    workflow.add_step(
        operation=amsc_extraction,
        inputs=amsc_inputs,
        depends_on=['chrome_setup'],
        batch_config=batch_config
    )
    
    # Step 3: Supabase Upload (processes all results)
    supabase_upload = SupabaseUploadOperation()
    
    upload_inputs = {
        'batch_size': batch_size,
        'table_name': 'rfq_index_extract'
    }
    
    workflow.add_step(
        operation=supabase_upload,
        inputs=upload_inputs,
        depends_on=['amsc_extraction'],
        batch_config={}
    )
    
    logger.info("Batch NSN AMSC extraction workflow created successfully")
    return workflow

def execute_batch_nsn_amsc_workflow(nsn_list: List[str], contract_ids: List[str] = None,
                                   headless: bool = True, timeout: int = 30,
                                   retry_attempts: int = 3, batch_size: int = 50) -> Dict[str, Any]:
    """
    Execute the batch NSN AMSC extraction workflow.
    
    Args:
        nsn_list: List of NSNs to process
        contract_ids: Optional list of contract IDs corresponding to NSNs
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        retry_attempts: Number of retry attempts for each NSN
        batch_size: Size of batches for database uploads
        
    Returns:
        Dictionary containing workflow results and summary
    """
    
    try:
        # Create workflow
        workflow = create_batch_nsn_amsc_workflow(
            nsn_list=nsn_list,
            contract_ids=contract_ids,
            headless=headless,
            timeout=timeout,
            retry_attempts=retry_attempts,
            batch_size=batch_size
        )
        
        # Execute workflow
        logger.info("Starting batch NSN AMSC extraction workflow execution")
        results = workflow.execute()
        
        # Get workflow status
        status = workflow.get_status()
        context = workflow.get_context()
        
        # Prepare summary
        summary = {
            'workflow_name': workflow.name,
            'status': status.value,
            'total_nsns': len(nsn_list),
            'steps_executed': len(results),
            'results': results,
            'context': context
        }
        
        # Add step-specific summaries
        if len(results) >= 3:
            # Chrome setup results
            chrome_result = results[0]
            summary['chrome_setup'] = {
                'success': chrome_result.success,
                'status': chrome_result.status.value,
                'metadata': chrome_result.metadata
            }
            
            # AMSC extraction results
            amsc_result = results[1]
            if amsc_result.success and amsc_result.data:
                summary['amsc_extraction'] = {
                    'success': amsc_result.success,
                    'status': amsc_result.status.value,
                    'total_items': amsc_result.data.get('total_items', 0),
                    'successful_items': amsc_result.data.get('successful_items', 0),
                    'failed_items': amsc_result.data.get('failed_items', 0)
                }
            
            # Supabase upload results
            upload_result = results[2]
            if upload_result.success and upload_result.data:
                summary['supabase_upload'] = {
                    'success': upload_result.success,
                    'status': upload_result.status.value,
                    'total_results': upload_result.data.get('total_results', 0),
                    'successful_uploads': upload_result.data.get('successful_uploads', 0),
                    'failed_uploads': upload_result.data.get('failed_uploads', 0)
                }
        
        logger.info(f"Batch NSN AMSC extraction workflow completed with status: {status.value}")
        
        return summary
        
    except Exception as e:
        error_msg = f"Batch NSN AMSC extraction workflow failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'workflow_name': 'batch_nsn_amsc_extraction',
            'status': 'failed',
            'error': error_msg,
            'total_nsns': len(nsn_list) if 'nsn_list' in locals() else 0
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
    parser = argparse.ArgumentParser(description="Batch extract AMSC codes from multiple NSNs")
    parser.add_argument("nsns", nargs="+", help="List of NSNs to process")
    parser.add_argument("--contract-ids", nargs="*", help="Optional list of contract IDs corresponding to NSNs")
    parser.add_argument("--headless", action="store_true", default=True, help="Run Chrome in headless mode (default: True)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for page operations in seconds (default: 30)")
    parser.add_argument("--retry-attempts", type=int, default=3, help="Number of retry attempts for each NSN (default: 3)")
    parser.add_argument("--batch-size", type=int, default=50, help="Size of batches for database uploads (default: 50)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate contract IDs if provided
    if args.contract_ids and len(args.contract_ids) != len(args.nsns):
        logger.error("Number of contract IDs must match number of NSNs")
        sys.exit(1)
    
    logger.info(f"Processing {len(args.nsns)} NSNs for AMSC extraction")
    if args.contract_ids:
        logger.info(f"Contract IDs provided: {len(args.contract_ids)}")
    
    # Execute workflow
    result = execute_batch_nsn_amsc_workflow(
        nsn_list=args.nsns,
        contract_ids=args.contract_ids,
        headless=args.headless,
        timeout=args.timeout,
        retry_attempts=args.retry_attempts,
        batch_size=args.batch_size
    )
    
    # Output results
    if result['status'] == 'completed':
        logger.info("Batch NSN AMSC extraction completed successfully")
        
        # Print summary
        if 'amsc_extraction' in result:
            amsc_summary = result['amsc_extraction']
            logger.info(f"AMSC Extraction: {amsc_summary['successful_items']}/{amsc_summary['total_items']} successful")
        
        if 'supabase_upload' in result:
            upload_summary = result['supabase_upload']
            logger.info(f"Database Upload: {upload_summary['successful_uploads']}/{upload_summary['total_results']} successful")
        
        sys.exit(0)
    else:
        logger.error(f"Batch NSN AMSC extraction failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
