#!/usr/bin/env python3
"""
Focused Debug Program for Workflow Upsert Error

This program replicates the exact upsert step from the universal_contract_queue_data_pull workflow
to isolate and debug the specific error occurring during the database update.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.uploaders.supabase_uploader import SupabaseUploader
from core.operations.supabase_upload_operation import SupabaseUploadOperation
from utils.logger import setup_logger

logger = setup_logger(__name__)


def debug_workflow_upsert():
    """Debug the exact upsert step from the workflow."""
    
    try:
        logger.info("🔍 Starting Workflow Upsert Debug Session")
        
        # Step 1: Initialize Supabase client (same as workflow)
        logger.info("Step 1: Initializing Supabase client")
        supabase_client = SupabaseUploader().supabase
        
        if not supabase_client:
            logger.error("❌ Failed to initialize Supabase client")
            return
        
        logger.info("✅ Supabase client initialized")
        
        # Step 2: Query contracts needing processing (same as workflow)
        logger.info("Step 2: Querying contracts needing processing")
        
        try:
            result = supabase_client.table('universal_contract_queue').select(
                "id,rfq_index_extract!inner(cde_g,solicitation_number,national_stock_number)"
            ).limit(3).execute()
            
            if not result.data:
                logger.info("No contracts found in universal_contract_queue")
                return
            
            logger.info(f"Found {len(result.data)} contracts for testing")
            
            # Log the structure of the first contract (same as workflow)
            first_contract = result.data[0]
            logger.info(f"Sample contract structure: {first_contract}")
            logger.info(f"Contract ID: {first_contract.get('id')}")
            logger.info(f"Solicitation Number: {first_contract.get('rfq_index_extract', {}).get('solicitation_number')}")
            logger.info(f"National Stock Number: {first_contract.get('rfq_index_extract', {}).get('national_stock_number')}")
            
        except Exception as e:
            logger.error(f"❌ Error querying contracts: {str(e)}")
            return
        
        # Step 3: Prepare upload data (same logic as workflow)
        logger.info("Step 3: Preparing upload data")
        
        upload_data = []
        for contract in result.data:
            contract_id = contract['id']
            rie_data = contract['rfq_index_extract']
            cde_g = rie_data.get('cde_g')
            
            # Check if AMSC code is missing (same logic as workflow)
            if not cde_g or (isinstance(cde_g, str) and cde_g.strip() == ''):
                contract_data = {
                    'id': contract_id,
                    'solicitation_number': rie_data.get('solicitation_number'),
                    'national_stock_number': rie_data.get('national_stock_number')
                }
                
                # Simulate the workflow's data preparation
                if contract_data.get('solicitation_number'):
                    tmp = {
                        'solicitation_number': contract_data['solicitation_number'],
                        'national_stock_number': contract_data['national_stock_number'],
                        'cde_g': 'TEST-AMSC',  # Simulate extracted AMSC code
                        'closed': False  # Simulate closed status
                    }
                    upload_data.append(tmp)
                    logger.info(f"Prepared upload data for SN: {contract_data['solicitation_number']}, NSN: {contract_data['national_stock_number']}")
                else:
                    logger.warning(f"Missing solicitation number for contract {contract_id}, skipping upload")
        
        if not upload_data:
            logger.info("ℹ️ No data to upload")
            return
        
        logger.info(f"Prepared {len(upload_data)} records for upload")
        
        # Log the first few records for debugging (same as workflow)
        for i, record in enumerate(upload_data[:3]):
            logger.info(f"Sample record {i+1}: {record}")
        
        # Step 4: Execute the exact upload operation from workflow
        logger.info("Step 4: Executing upload operation (exact workflow parameters)")
        
        upload_op = SupabaseUploadOperation()
        
        # Use the exact parameters from the workflow
        workflow_inputs = {
            'results': upload_data,
            'table_name': 'rfq_index_extract',
            'operation_type': 'upsert',
            'upsert_strategy': 'merge',
            'conflict_resolution': 'update_existing',
            'key_fields': ['solicitation_number', 'national_stock_number'],  # Exact key fields from workflow
            'batch_size': 50
        }
        
        logger.info(f"Workflow inputs: {workflow_inputs}")
        
        try:
            logger.info("Attempting to upload records to database...")
            
            upload_result = upload_op._execute(workflow_inputs, {})
            
            logger.info(f"Upload operation completed. Success: {upload_result.success}")
            
            if upload_result.success:
                logger.info(f"✅ Database upload completed: {len(upload_data)} records")
                if hasattr(upload_result, 'data') and upload_result.data:
                    logger.info(f"Upload result data: {upload_result.data}")
            else:
                logger.error(f"❌ Database upload failed: {upload_result.error}")
                # Log more details about the failure (same as workflow)
                if hasattr(upload_result, 'data') and upload_result.data:
                    logger.error(f"Upload result data: {upload_result.data}")
                if hasattr(upload_result, 'metadata') and upload_result.metadata:
                    logger.error(f"Upload result metadata: {upload_result.metadata}")
                    
        except Exception as upload_error:
            logger.error(f"❌ Exception during upload operation: {str(upload_error)}")
            import traceback
            logger.error(f"Upload error traceback: {traceback.format_exc()}")
        
        # Step 5: Test individual upsert calls to isolate the issue
        logger.info("Step 5: Testing individual upsert calls")
        
        for i, record in enumerate(upload_data[:2]):  # Test first 2 records
            logger.info(f"Testing individual upsert for record {i+1}: {record}")
            
            try:
                # Test the exact Supabase upsert call that the operation uses
                table = supabase_client.table('rfq_index_extract')
                
                # Use the exact syntax from the operation
                result = table.upsert(
                    record, 
                    on_conflict=','.join(['solicitation_number', 'national_stock_number'])
                ).execute()
                
                logger.info(f"  ✅ Individual upsert {i+1} successful")
                logger.info(f"  Result data: {result.data}")
                logger.info(f"  Result count: {getattr(result, 'count', 'N/A')}")
                
            except Exception as e:
                logger.error(f"  ❌ Individual upsert {i+1} failed: {str(e)}")
                import traceback
                logger.error(f"  Traceback: {traceback.format_exc()}")
                
                # Additional debugging for the specific error
                logger.error(f"  Error type: {type(e).__name__}")
                logger.error(f"  Error args: {e.args}")
                
                # Check if it's a Supabase-specific error
                if hasattr(e, 'code'):
                    logger.error(f"  Supabase error code: {e.code}")
                if hasattr(e, 'message'):
                    logger.error(f"  Supabase error message: {e.message}")
                if hasattr(e, 'details'):
                    logger.error(f"  Supabase error details: {e.details}")
        
        logger.info("🔍 Workflow Upsert Debug Session completed")
        
    except Exception as e:
        logger.error(f"❌ Debug session failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


def main():
    """Main entry point."""
    logger.info("🚀 Starting Workflow Upsert Debug Program")
    
    try:
        debug_workflow_upsert()
        logger.info("✅ Debug program completed successfully")
    except Exception as e:
        logger.error(f"❌ Debug program failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
