"""
Supabase Upload Operation
Handles uploading processed data to Supabase database with support for upsert operations
"""

from typing import Dict, Any, List, Optional
import logging
from supabase import create_client, Client
from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class SupabaseUploadOperation(BaseOperation):
    """
    Operation that uploads batch results to Supabase database.
    
    This operation:
    1. Connects to Supabase using environment variables
    2. Processes batch results from previous operations
    3. Supports both update and upsert operations
    4. Handles both individual and batch uploads
    5. Can work with different table schemas
    """
    
    def __init__(self):
        """Initialize the Supabase upload operation."""
        super().__init__(
            name="supabase_upload",
            description="Upload batch results to Supabase database with upsert support"
        )
        
        # Set required inputs
        self.set_required_inputs(['results'])
        
        # Set optional inputs
        self.set_optional_inputs([
            'batch_size', 
            'table_name', 
            'operation_type', 
            'upsert_strategy',
            'conflict_resolution',
            'key_fields'
        ])
        
        # Initialize Supabase client
        self.supabase: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client."""
        try:
            import os
            from pathlib import Path
            import dotenv
            
            # Try to load from .env file if it exists
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            env_file = project_root / '.env'
            
            # Also check etl/ subdirectory (GitHub Actions case)
            if not env_file.exists():
                etl_env_file = current_file.parent.parent.parent / '.env'
                if etl_env_file.exists():
                    env_file = etl_env_file
            
            # Load .env file if it exists
            if env_file.exists():
                logger.info(f"Loading environment from: {env_file}")
                dotenv.load_dotenv(env_file)
                logger.info("Environment file loaded successfully")
            else:
                logger.info("No .env file found, using system environment variables")
            
            # Get environment variables
            supabase_url = os.getenv('VITE_SUPABASE_URL')
            service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            publishable_key = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
            
            logger.info(f"Environment variables loaded:")
            logger.info(f"  VITE_SUPABASE_URL: {'✓' if supabase_url else '✗'}")
            logger.info(f"  SUPABASE_SERVICE_ROLE_KEY: {'✓' if service_role_key else '✗'}")
            logger.info(f"  VITE_SUPABASE_PUBLISHABLE_KEY: {'✓' if publishable_key else '✗'}")
            
            # Use service role key first, then fallback to publishable key
            supabase_key = service_role_key or publishable_key
            
            if not supabase_url or not supabase_key:
                logger.error("Missing required Supabase environment variables")
                raise ValueError("Missing Supabase environment variables")
            
            # Create client
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the Supabase upload operation.
        
        Args:
            inputs: Operation inputs containing 'results' and optionally 'batch_size'
            context: Shared workflow context
            
        Returns:
            OperationResult with upload success status and metadata
        """
        if not self.supabase:
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error="Supabase client not initialized",
                metadata={'client_initialized': False}
            )
            
        try:
            results = inputs['results']
            batch_size = inputs.get('batch_size', 50)
            table_name = inputs.get('table_name', 'rfq_index_extract')
            operation_type = inputs.get('operation_type', 'upsert')  # 'upsert' or 'update'
            upsert_strategy = inputs.get('upsert_strategy', 'merge')  # 'merge' or 'ignore'
            conflict_resolution = inputs.get('conflict_resolution', 'update_existing')
            key_fields = inputs.get('key_fields', ['national_stock_number'])  # Fields to use for conflict resolution
            
            if not results:
                logger.warning("No results to upload")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={'uploaded_count': 0},
                    metadata={'message': 'No results to upload'}
                )
            
            logger.info(f"Uploading {len(results)} results to Supabase table: {table_name}")
            logger.info(f"Operation type: {operation_type}, Strategy: {upsert_strategy}")
            
            # Process results in batches
            successful_uploads = 0
            failed_uploads = 0
            upload_errors = []
            
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} items")
                
                if operation_type == 'upsert':
                    batch_results = self._upsert_batch(batch, table_name, upsert_strategy, conflict_resolution, key_fields)
                else:
                    # Fallback to legacy update method for backward compatibility
                    batch_results = self._upload_batch(batch, table_name)
                
                successful_uploads += batch_results['successful']
                failed_uploads += batch_results['failed']
                upload_errors.extend(batch_results['errors'])
            
            logger.info(f"Upload completed. Successful: {successful_uploads}, Failed: {failed_uploads}")
            
            return OperationResult(
                success=failed_uploads == 0,
                status=OperationStatus.COMPLETED if failed_uploads == 0 else OperationStatus.FAILED,
                data={
                    'total_results': len(results),
                    'successful_uploads': successful_uploads,
                    'failed_uploads': failed_uploads,
                    'upload_errors': upload_errors
                },
                metadata={
                    'table_name': table_name,
                    'batch_size_used': batch_size,
                    'operation_type': operation_type,
                    'upsert_strategy': upsert_strategy
                }
            )
            
        except Exception as e:
            error_msg = f"Supabase upload failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def _upsert_batch(self, batch: List[Dict[str, Any]], table_name: str, 
                      upsert_strategy: str, conflict_resolution: str, 
                      key_fields: List[str]) -> Dict[str, Any]:
        """
        Upsert a batch of results to Supabase.
        
        Args:
            batch: List of result dictionaries
            table_name: Name of the table to upload to
            upsert_strategy: Strategy for handling duplicates ('merge' or 'ignore')
            conflict_resolution: How to resolve conflicts ('update_existing' or 'skip_existing')
            key_fields: Fields to use for conflict resolution
            
        Returns:
            Dictionary with upload results
        """
        successful = 0
        failed = 0
        errors = []
        
        for result in batch:
            try:
                if not result.get('success', False):
                    logger.warning(f"Skipping failed result: {result.get('error', 'Unknown error')}")
                    failed += 1
                    continue
                
                # Extract data from result
                data = result.get('data', {})
                
                if not data:
                    logger.warning("No data found in result")
                    failed += 1
                    continue
                
                # Validate key fields exist
                missing_keys = [key for key in key_fields if key not in data or data[key] is None]
                if missing_keys:
                    logger.warning(f"Missing key fields: {missing_keys}")
                    failed += 1
                    continue
                
                # Perform upsert operation
                upsert_success = self._perform_upsert(data, table_name, upsert_strategy, conflict_resolution, key_fields)
                
                if upsert_success:
                    successful += 1
                    logger.info(f"Successfully upserted record with keys: {[data.get(k) for k in key_fields]}")
                else:
                    failed += 1
                    errors.append(f"Failed to upsert record with keys: {[data.get(k) for k in key_fields]}")
                    
            except Exception as e:
                failed += 1
                error_msg = f"Error processing result: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _perform_upsert(self, data: Dict[str, Any], table_name: str, 
                        upsert_strategy: str, conflict_resolution: str, 
                        key_fields: List[str]) -> bool:
        """
        Perform the actual upsert operation.
        
        Args:
            data: Data to upsert
            table_name: Name of the table
            upsert_strategy: Strategy for handling duplicates
            conflict_resolution: How to resolve conflicts
            key_fields: Fields to use for conflict resolution
            
        Returns:
            True if upsert successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Build the upsert query
            query = self.supabase.table(table_name)
            
            if upsert_strategy == 'merge':
                # Use upsert with conflict resolution
                if conflict_resolution == 'update_existing':
                    # Update existing records, insert new ones
                    result = query.upsert(data, on_conflict=','.join(key_fields)).execute()
                else:
                    # Skip existing records, only insert new ones
                    result = query.insert(data).execute()
            else:  # ignore strategy
                # Only insert if no conflicts
                result = query.insert(data).execute()
            
            if result.data:
                logger.debug(f"Upsert successful for keys: {[data.get(k) for k in key_fields]}")
                return True
            else:
                logger.warning(f"No records affected for keys: {[data.get(k) for k in key_fields]}")
                return False
                
        except Exception as e:
            logger.error(f"Error performing upsert: {str(e)}")
            return False
    
    def _upload_batch(self, batch: List[Dict[str, Any]], table_name: str) -> Dict[str, Any]:
        """
        Upload a batch of results to Supabase (legacy method for backward compatibility).
        
        Args:
            batch: List of result dictionaries
            table_name: Name of the table to upload to
            
        Returns:
            Dictionary with upload results
        """
        successful = 0
        failed = 0
        errors = []
        
        for result in batch:
            try:
                if not result.get('success', False):
                    logger.warning(f"Skipping failed result: {result.get('error', 'Unknown error')}")
                    failed += 1
                    continue
                
                # Extract data from result
                data = result.get('data', {})
                nsn = data.get('nsn')
                amsc_code = data.get('amsc_code')
                is_closed = data.get('is_closed')
                contract_id = data.get('contract_id')
                
                if not all([nsn, amsc_code]):
                    logger.warning(f"Incomplete data for upload: NSN={nsn}, AMSC={amsc_code}")
                    failed += 1
                    continue
                
                # Update the database
                update_success = self._update_amsc_and_closed_status(
                    contract_id, nsn, amsc_code, is_closed, table_name
                )
                
                if update_success:
                    successful += 1
                    logger.info(f"Successfully updated NSN {nsn} with AMSC code {amsc_code}")
                else:
                    failed += 1
                    errors.append(f"Failed to update NSN {nsn}")
                    
            except Exception as e:
                failed += 1
                error_msg = f"Error processing result: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _update_amsc_and_closed_status(self, contract_id: str, nsn: str, amsc_code: str, 
                                      is_closed: bool, table_name: str) -> bool:
        """
        Update AMSC code and closed status in the database (legacy method).
        
        Args:
            contract_id: Contract ID to update
            nsn: National Stock Number
            amsc_code: Extracted AMSC code
            is_closed: Whether solicitations are closed
            table_name: Name of the table to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Prepare update data
            update_data = {
                'cde_g': amsc_code,
                'closed': is_closed if is_closed is not None else None
            }
            
            # Update the record
            if contract_id:
                # Update by contract ID
                result = self.supabase.table(table_name).update(update_data).eq('id', contract_id).execute()
            else:
                # Update by NSN if no contract ID
                result = self.supabase.table(table_name).update(update_data).eq('national_stock_number', nsn).execute()
            
            if result.data:
                logger.info(f"Database updated successfully for NSN {nsn}")
                return True
            else:
                logger.warning(f"No records updated for NSN {nsn}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating database for NSN {nsn}: {str(e)}")
            return False
    
    def can_apply_to_batch(self) -> bool:
        """
        Supabase upload can be applied to batches.
        
        Returns:
            True - this operation supports batch processing
        """
        return True
    
    def apply_to_batch(self, items: List[Any], inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[OperationResult]:
        """
        Apply Supabase upload to a batch of items.
        
        Args:
            items: List of items to process
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each item
        """
        if context is None:
            context = {}
        
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} items for Supabase upload")
        
        for i, item in enumerate(items, 1):
            logger.info(f"Processing item {i}/{total_items}")
            
            # Create item-specific inputs
            item_inputs = inputs.copy()
            item_inputs['results'] = [item]  # Single item as results list
            
            # Execute operation for this item
            result = self.execute(item_inputs, context)
            results.append(result)
        
        logger.info(f"Batch processing completed. {len([r for r in results if r.success])}/{total_items} successful")
        return results
