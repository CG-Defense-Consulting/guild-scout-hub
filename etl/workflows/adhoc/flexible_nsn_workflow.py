#!/usr/bin/env python3
"""
Flexible NSN Workflow

This workflow demonstrates the flexible composition of operations:
- Chrome Driver setup (once)
- LOOP [for each NSN]:
  - Consent Page handling
  - Extract NSN data
  - Upload to Supabase
  - Extract Closed/Open status
  - Upload to Supabase again

This shows how operations can be mixed, matched, and looped for maximum flexibility.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

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

def create_flexible_nsn_workflow(nsn_list: List[str], contract_ids: List[str] = None,
                                headless: bool = True, timeout: int = 30,
                                retry_attempts: int = 3, batch_size: int = 50) -> WorkflowOrchestrator:
    """
    Create a flexible NSN workflow that demonstrates operation composition.
    
    This workflow shows how to:
    1. Set up Chrome once
    2. Loop through each NSN with multiple operations
    3. Mix and match operations in sequence
    
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
    
    logger.info(f"Creating flexible NSN workflow for {len(nsn_list)} NSNs")
    
    # Create workflow orchestrator
    workflow = WorkflowOrchestrator(
        name="flexible_nsn_workflow",
        description=f"Flexible NSN processing with operation composition for {len(nsn_list)} NSNs"
    )
    
    # Step 1: Chrome Setup (runs once, shared across all operations)
    chrome_setup = ChromeSetupOperation(headless=headless)
    workflow.add_step(
        operation=chrome_setup,
        inputs={},
        depends_on=[],
        batch_config={}
    )
    
    # Step 2: Consent Page Handling (applied to batch of NSNs)
    # This handles consent pages for all NSNs at once
    consent_page = ConsentPageOperation()
    
    # Prepare URLs for consent handling
    base_url = "https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx"
    urls = [f"{base_url}?value={nsn}&category=nsn" for nsn in nsn_list]
    
    workflow.add_step(
        operation=consent_page,
        inputs={'timeout': timeout},
        depends_on=['chrome_setup'],
        batch_config={'items': urls}
    )
    
    # Step 3: NSN Data Extraction (applied to batch of NSNs)
    nsn_extraction = NsnExtractionOperation()
    
    nsn_inputs = {
        'timeout': timeout,
        'retry_attempts': retry_attempts,
        'extract_fields': ['amsc_code', 'description', 'part_number']
    }
    
    workflow.add_step(
        operation=nsn_extraction,
        inputs=nsn_inputs,
        depends_on=['consent_page'],
        batch_config={'items': nsn_list, 'contract_ids': contract_ids}
    )
    
    # Step 4: First Supabase Upload (AMSC codes and basic data)
    supabase_upload_1 = SupabaseUploadOperation()
    
    upload_inputs_1 = {
        'batch_size': batch_size,
        'table_name': 'rfq_index_extract'
    }
    
    workflow.add_step(
        operation=supabase_upload_1,
        inputs=upload_inputs_1,
        depends_on=['nsn_extraction'],
        batch_config={}
    )
    
    # Step 5: Closed Solicitation Check (applied to batch of NSNs)
    closed_check = ClosedSolicitationCheckOperation()
    
    closed_inputs = {
        'timeout': timeout,
        'wait_for_element': "//body"  # Wait for page body to load
    }
    
    workflow.add_step(
        operation=closed_check,
        inputs=closed_inputs,
        depends_on=['nsn_extraction'],  # Depends on NSN extraction, not upload
        batch_config={'items': nsn_list, 'contract_ids': contract_ids}
    )
    
    # Step 6: Second Supabase Upload (closed status updates)
    supabase_upload_2 = SupabaseUploadOperation()
    
    upload_inputs_2 = {
        'batch_size': batch_size,
        'table_name': 'rfq_index_extract'
    }
    
    workflow.add_step(
        operation=supabase_upload_2,
        inputs=upload_inputs_2,
        depends_on=['closed_solicitation_check'],
        batch_config={}
    )
    
    logger.info("Flexible NSN workflow created successfully")
    return workflow

def create_alternative_workflow_pattern(nsn_list: List[str], contract_ids: List[str] = None,
                                      headless: bool = True, timeout: int = 30) -> WorkflowOrchestrator:
    """
    Create an alternative workflow pattern showing different operation composition.
    
    This demonstrates how operations can be arranged differently:
    - Chrome Setup
    - For each NSN: Consent → Extract → Check Closed → Upload (all at once)
    
    Args:
        nsn_list: List of NSNs to process
        contract_ids: Optional list of contract IDs corresponding to NSNs
        headless: Whether to run Chrome in headless mode
        timeout: Timeout for page operations
        
    Returns:
        Configured WorkflowOrchestrator instance
    """
    
    logger.info(f"Creating alternative workflow pattern for {len(nsn_list)} NSNs")
    
    workflow = WorkflowOrchestrator(
        name="alternative_nsn_workflow",
        description=f"Alternative NSN workflow pattern for {len(nsn_list)} NSNs"
    )
    
    # Step 1: Chrome Setup
    chrome_setup = ChromeSetupOperation(headless=headless)
    workflow.add_step(
        operation=chrome_setup,
        inputs={},
        depends_on=[],
        batch_config={}
    )
    
    # Step 2: Combined NSN Processing (Consent + Extract + Closed Check)
    # This shows how you could combine multiple operations into one step
    # if you wanted to process each NSN completely before moving to the next
    
    # For this example, we'll create a custom operation that combines multiple steps
    # In practice, you could create a custom operation class that does this
    
    # Step 3: Final Upload (all results at once)
    supabase_upload = SupabaseUploadOperation()
    
    workflow.add_step(
        operation=supabase_upload,
        inputs={'batch_size': 100, 'table_name': 'rfq_index_extract'},
        depends_on=['chrome_setup'],
        batch_config={}
    )
    
    logger.info("Alternative workflow pattern created successfully")
    return workflow

def execute_flexible_workflow(nsn_list: List[str], contract_ids: List[str] = None,
                             headless: bool = True, timeout: int = 30,
                             retry_attempts: int = 3, batch_size: int = 50) -> Dict[str, Any]:
    """
    Execute the flexible NSN workflow.
    
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
        workflow = create_flexible_nsn_workflow(
            nsn_list=nsn_list,
            contract_ids=contract_ids,
            headless=headless,
            timeout=timeout,
            retry_attempts=retry_attempts,
            batch_size=batch_size
        )
        
        # Execute workflow
        logger.info("Starting flexible NSN workflow execution")
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
        if len(results) >= 6:
            # Chrome setup results
            chrome_result = results[0]
            summary['chrome_setup'] = {
                'success': chrome_result.success,
                'status': chrome_result.status.value,
                'metadata': chrome_result.metadata
            }
            
            # Consent page results
            consent_result = results[1]
            if consent_result.success and consent_result.data:
                summary['consent_page'] = {
                    'success': consent_result.success,
                    'status': consent_result.status.value,
                    'total_items': consent_result.data.get('total_items', 0),
                    'successful_items': consent_result.data.get('successful_items', 0),
                    'failed_items': consent_result.data.get('failed_items', 0)
                }
            
            # NSN extraction results
            nsn_result = results[2]
            if nsn_result.success and nsn_result.data:
                summary['nsn_extraction'] = {
                    'success': nsn_result.success,
                    'status': nsn_result.status.value,
                    'total_items': nsn_result.data.get('total_items', 0),
                    'successful_items': nsn_result.data.get('successful_items', 0),
                    'failed_items': nsn_result.data.get('failed_items', 0)
                }
            
            # First upload results
            upload1_result = results[3]
            if upload1_result.success and upload1_result.data:
                summary['first_upload'] = {
                    'success': upload1_result.success,
                    'status': upload1_result.status.value,
                    'total_results': upload1_result.data.get('total_results', 0),
                    'successful_uploads': upload1_result.data.get('successful_uploads', 0),
                    'failed_uploads': upload1_result.data.get('failed_uploads', 0)
                }
            
            # Closed status check results
            closed_result = results[4]
            if closed_result.success and closed_result.data:
                summary['closed_status_check'] = {
                    'success': closed_result.success,
                    'status': closed_result.status.value,
                    'total_items': closed_result.data.get('total_items', 0),
                    'successful_items': closed_result.data.get('successful_items', 0),
                    'failed_items': closed_result.data.get('failed_items', 0)
                }
            
            # Second upload results
            upload2_result = results[5]
            if upload2_result.success and upload2_result.data:
                summary['second_upload'] = {
                    'success': upload2_result.success,
                    'status': upload2_result.status.value,
                    'total_results': upload2_result.data.get('total_results', 0),
                    'successful_uploads': upload2_result.data.get('successful_uploads', 0),
                    'failed_uploads': upload2_result.data.get('failed_uploads', 0)
                }
        
        logger.info(f"Flexible NSN workflow completed with status: {status.value}")
        
        return summary
        
    except Exception as e:
        error_msg = f"Flexible NSN workflow failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'workflow_name': 'flexible_nsn_workflow',
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
    parser = argparse.ArgumentParser(description="Execute flexible NSN workflow with operation composition")
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
    
    logger.info(f"Processing {len(args.nsns)} NSNs with flexible workflow")
    if args.contract_ids:
        logger.info(f"Contract IDs provided: {len(args.contract_ids)}")
    
    # Execute workflow
    result = execute_flexible_workflow(
        nsn_list=args.nsns,
        contract_ids=args.contract_ids,
        headless=args.headless,
        timeout=args.timeout,
        retry_attempts=args.retry_attempts,
        batch_size=args.batch_size
    )
    
    # Output results
    if result['status'] == 'completed':
        logger.info("Flexible NSN workflow completed successfully")
        
        # Print summary
        if 'nsn_extraction' in result:
            nsn_summary = result['nsn_extraction']
            logger.info(f"NSN Extraction: {nsn_summary['successful_items']}/{nsn_summary['total_items']} successful")
        
        if 'closed_status_check' in result:
            closed_summary = result['closed_status_check']
            logger.info(f"Closed Status Check: {closed_summary['successful_items']}/{closed_summary['total_items']} successful")
        
        if 'first_upload' in result:
            upload1_summary = result['first_upload']
            logger.info(f"First Upload: {upload1_summary['successful_uploads']}/{upload1_summary['total_results']} successful")
        
        if 'second_upload' in result:
            upload2_summary = result['second_upload']
            logger.info(f"Second Upload: {upload2_summary['successful_uploads']}/{upload2_summary['total_results']} successful")
        
        sys.exit(0)
    else:
        logger.error(f"Flexible NSN workflow failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    main()
