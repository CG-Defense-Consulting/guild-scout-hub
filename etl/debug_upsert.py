#!/usr/bin/env python3
"""
Temporary Debug Program for Supabase Upsert Error

This program isolates the upsert step from the universal_contract_queue_data_pull workflow
to help debug the specific error occurring during the database update.
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


def debug_upsert_step():
    """Debug the upsert step with sample data and detailed error logging."""
    
    try:
        logger.info("🔍 Starting Supabase Upsert Debug Session")
        
        # Step 1: Initialize Supabase client
        logger.info("Step 1: Initializing Supabase client")
        supabase_client = SupabaseUploader().supabase
        
        if not supabase_client:
            logger.error("❌ Failed to initialize Supabase client")
            return
        
        logger.info("✅ Supabase client initialized successfully")
        
        # Step 2: Test basic connection
        logger.info("Step 2: Testing basic Supabase connection")
        try:
            # Try a simple query to test connection
            result = supabase_client.table('rfq_index_extract').select('id').limit(1).execute()
            logger.info(f"✅ Connection test successful. Sample data: {result.data[:2] if result.data else 'No data'}")
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return
        
        # Step 3: Create sample data that matches the workflow
        logger.info("Step 3: Creating sample data for upsert test")
        
        # This is the exact data structure that the workflow is trying to upsert
        sample_upload_data = [
            {
                'solicitation_number': 'TEST-SN-001',
                'national_stock_number': 'TEST-NSN-001',
                'cde_g': 'G',
                'closed': False
            },
            {
                'solicitation_number': 'TEST-SN-002',
                'national_stock_number': 'TEST-NSN-002',
                'cde_g': 'A',
                'closed': True
            }
        ]
        
        logger.info(f"Sample upload data structure:")
        for i, record in enumerate(sample_upload_data):
            logger.info(f"  Record {i+1}: {record}")
        
        # Step 4: Test the upsert operation directly
        logger.info("Step 4: Testing upsert operation directly")
        
        upload_op = SupabaseUploadOperation()
        
        # Test with the exact parameters from the workflow
        test_inputs = {
            'results': sample_upload_data,
            'table_name': 'rfq_index_extract',
            'operation_type': 'upsert',
            'upsert_strategy': 'merge',
            'conflict_resolution': 'update_existing',
            #'key_fields': ['solicitation_number', 'national_stock_number', 'purchase_request_number'],
            'batch_size': 50
        }
        
        logger.info(f"Test inputs: {test_inputs}")
        
        # Execute the upload operation
        logger.info("Executing upload operation...")
        upload_result = upload_op._execute(test_inputs, {})
        
        logger.info(f"Upload operation completed:")
        logger.info(f"  Success: {upload_result.success}")
        logger.info(f"  Status: {upload_result.status}")
        logger.info(f"  Error: {upload_result.error if not upload_result.success else 'None'}")
        logger.info(f"  Data: {upload_result.data}")
        logger.info(f"  Metadata: {upload_result.metadata}")
        
        # Step 5: Test individual upsert operations
        logger.info("Step 5: Testing individual upsert operations")
        
        for i, record in enumerate(sample_upload_data):
            logger.info(f"Testing individual upsert for record {i+1}: {record}")
            
            try:
                # Test the actual Supabase upsert call
                table = supabase_client.table('rfq_index_extract')
                
                # Try the upsert with the exact syntax from the operation
                result = table.upsert(
                    record, 
                    #on_conflict=','.join(['solicitation_number', 'national_stock_number'])
                ).execute()
                
                logger.info(f"  ✅ Individual upsert {i+1} successful")
                logger.info(f"  Result data: {result.data}")
                logger.info(f"  Result count: {getattr(result, 'count', 'N/A')}")
                
            except Exception as e:
                logger.error(f"  ❌ Individual upsert {i+1} failed: {str(e)}")
                import traceback
                logger.error(f"  Traceback: {traceback.format_exc()}")
        
        # Step 6: Test table schema
        logger.info("Step 6: Testing table schema")
        
        try:
            # Get table info
            table_info = supabase_client.table('rfq_index_extract').select('*').limit(1).execute()
            logger.info(f"Table structure sample: {table_info.data[0] if table_info.data else 'No data'}")
            
            # Check if key fields exist
            if table_info.data:
                sample_record = table_info.data[0]
                logger.info(f"Available fields: {list(sample_record.keys())}")
                
                # Check for required fields
                required_fields = ['solicitation_number', 'national_stock_number', 'cde_g', 'closed']
                missing_fields = [field for field in required_fields if field not in sample_record]
                
                if missing_fields:
                    logger.warning(f"⚠️ Missing required fields: {missing_fields}")
                else:
                    logger.info("✅ All required fields are present")
                    
        except Exception as e:
            logger.error(f"❌ Error checking table schema: {str(e)}")
        
        # Step 7: Test with real data from the database
        logger.info("Step 7: Testing with real data from database")
        
        try:
            # Query for actual contracts that need processing
            result = supabase_client.table('universal_contract_queue').select(
                "id,rfq_index_extract!inner(cde_g,solicitation_number,national_stock_number)"
            ).limit(2).execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} real contracts for testing")
                
                # Convert to the format expected by the workflow
                real_upload_data = []
                for contract in result.data:
                    contract_id = contract['id']
                    rie_data = contract['rfq_index_extract']
                    
                    # Simulate the workflow's data preparation
                    if rie_data.get('solicitation_number') and rie_data.get('national_stock_number'):
                        upload_record = {
                            'id': contract_id,
                            'solicitation_number': rie_data['solicitation_number'],
                            'national_stock_number': rie_data['national_stock_number'],
                            'cde_g': 'TEST-AMSC',  # Test value
                            'closed': False  # Test value
                        }
                        real_upload_data.append(upload_record)
                        logger.info(f"Prepared real data: {upload_record}")
                
                if real_upload_data:
                    logger.info("Testing upsert with real data...")
                    
                    # Test the upsert operation with real data
                    real_upload_result = upload_op._execute({
                        'results': real_upload_data,
                        'table_name': 'rfq_index_extract',
                        'operation_type': 'upsert',
                        'upsert_strategy': 'merge',
                        'conflict_resolution': 'update_existing',
                        # 'key_fields': ['solicitation_number', 'national_stock_number'],
                        'batch_size': 50
                    }, {})
                    
                    logger.info(f"Real data upload result:")
                    logger.info(f"  Success: {real_upload_result.success}")
                    logger.info(f"  Error: {real_upload_result.error if not real_upload_result.success else 'None'}")
                    logger.info(f"  Data: {real_upload_result.data}")
                    
            else:
                logger.info("No real contracts found for testing")
                
        except Exception as e:
            logger.error(f"❌ Error testing with real data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info("🔍 Supabase Upsert Debug Session completed")
        
    except Exception as e:
        logger.error(f"❌ Debug session failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


def main():
    """Main entry point."""
    logger.info("🚀 Starting Supabase Upsert Debug Program")
    
    try:
        debug_upsert_step()
        logger.info("✅ Debug program completed successfully")
    except Exception as e:
        logger.error(f"❌ Debug program failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
