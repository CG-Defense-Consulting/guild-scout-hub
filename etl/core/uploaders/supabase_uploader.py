"""
Supabase Uploader
Handles uploading data to Supabase database and storage
"""

from typing import Dict, Any, Optional
import logging
import os
from pathlib import Path
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

logger = logging.getLogger(__name__)

class SupabaseUploader:
    """Handles uploading data to Supabase database and storage."""
    
    def __init__(self):
        """Initialize the Supabase uploader."""
        self.supabase: Optional[Client] = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the Supabase client."""
        try:
            # Load environment variables from parent directory .env file
            from pathlib import Path
            import dotenv
            
            # Look for .env file in parent directories
            current_file = Path(__file__).resolve()  # Get absolute path
            project_root = current_file.parent.parent.parent.parent  # Go up from core/uploaders/ to project root
            env_file = project_root / '.env'
            
            if env_file.exists():
                logger.info(f"Loading environment from: {env_file}")
                dotenv.load_dotenv(env_file)
                logger.info("Environment file loaded successfully")
            else:
                logger.warning(f"Environment file not found at: {env_file}")
            
            # Get environment variables
            supabase_url = os.getenv('VITE_SUPABASE_URL')
            logger.info(f"Supabase URL loaded: {'✓' if supabase_url else '✗'}")
            
            # Try service role key first (for ETL workflows), then fallback to publishable key
            service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            publishable_key = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
            
            logger.info(f"Service role key loaded: {'✓' if service_role_key else '✗'}")
            logger.info(f"Publishable key loaded: {'✓' if publishable_key else '✗'}")
            
            supabase_key = service_role_key or publishable_key
            
            if not supabase_url or not supabase_key:
                logger.error("Missing Supabase environment variables")
                raise ValueError("Missing Supabase environment variables")
            
            # Log which key type we're using (without exposing the key)
            if os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
                logger.info("Using Supabase service role key for authenticated access")
            else:
                logger.info("Using Supabase publishable key for anonymous access")
            
            # Create client
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def _find_contract_id(self, solicitation_number: str) -> Optional[str]:
        """
        Find the contract ID that matches the solicitation number.
        
        Args:
            solicitation_number: The solicitation number to search for
            
        Returns:
            Contract ID if found, None otherwise
        """
        try:
            # First, find the rfq_index_extract record by solicitation_number
            # Then check if there's a corresponding universal_contract_queue record
            result = self.supabase.table('rfq_index_extract').select('id').eq('solicitation_number', solicitation_number).execute()
            
            if result.data and len(result.data) > 0:
                rfq_id = result.data[0]['id']
                logger.info(f"Found RFQ ID {rfq_id} for solicitation {solicitation_number}")
                
                # Now check if there's a contract in the queue with this ID
                contract_result = self.supabase.table('universal_contract_queue').select('id').eq('id', rfq_id).execute()
                
                if contract_result.data and len(contract_result.data) > 0:
                    contract_id = contract_result.data[0]['id']
                    logger.info(f"Found contract ID {contract_id} for solicitation {solicitation_number}")
                    return contract_id
                else:
                    logger.warning(f"No contract in queue for RFQ ID {rfq_id}")
                    # Use the RFQ ID as fallback since it's the same ID that would be used
                    return rfq_id
            else:
                logger.warning(f"No RFQ record found for solicitation {solicitation_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding contract ID: {str(e)}")
            return None

    def upload_pdf_to_storage(self, pdf_path: str, solicitation_number: str) -> Optional[str]:
        """
        Upload PDF to Supabase storage bucket using the same approach as the UI.
        
        Args:
            pdf_path: Path to the PDF file
            solicitation_number: Solicitation number for naming
            
        Returns:
            Storage path if successful, None otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return None
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            # Validate that the file is actually a PDF by checking magic bytes
            try:
                with open(pdf_path, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        logger.error(f"File does not contain valid PDF header. Got: {header}")
                        return None
                    logger.info("✓ PDF header validation passed")
            except Exception as e:
                logger.error(f"Error validating PDF header: {str(e)}")
                return None
            
            # Find the contract ID for this solicitation number
            contract_id = self._find_contract_id(solicitation_number)
            if not contract_id:
                logger.warning(f"Using solicitation number as fallback for file naming")
                contract_id = solicitation_number
            
            # Create unique filename using the same format as UI
            # Format timestamp to match Supabase storage expectations
            timestamp = self._get_timestamp().replace(':', '-').replace('.', '-')
            file_extension = Path(pdf_path).suffix.lower()  # Ensure lowercase extension
            
            # Validate that this is actually a PDF file
            if file_extension not in ['.pdf', '.PDF']:
                logger.warning(f"File extension '{file_extension}' is not a PDF. Expected .pdf or .PDF")
                # Force .pdf extension for consistency
                file_extension = '.pdf'
            
            # Format: contract-{contractId}-{timestamp}-{encodedOriginalName}.{extension}
            # This matches the UI format: contract-{contractId}-{timestamp}-{encodedOriginalName}.{extension}
            # Encode the solicitation number as the original filename so the UI displays it properly
            encoded_solicitation = solicitation_number.replace('(', '_').replace(')', '_')
            unique_filename = f"contract-{contract_id}-{timestamp}-{encoded_solicitation}{file_extension}"
            
            # Upload to Supabase storage using the same approach as UI
            logger.info(f"Uploading PDF to storage: {unique_filename}")
            logger.info(f"PDF path for upload: {pdf_path}")
            logger.info(f"PDF path type: {type(pdf_path)}")
            
            # Upload file as binary data to preserve content type
            try:
                logger.info("Getting storage bucket...")
                bucket = self.supabase.storage.from_('docs')
                logger.info("✓ Storage bucket obtained")
                
                logger.info("Reading PDF file as binary data...")
                # Read the file as binary data to preserve content type
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                
                logger.info(f"PDF data size: {len(pdf_data)} bytes")
                logger.info(f"PDF data type: {type(pdf_data)}")
                
                logger.info("Calling upload method with binary data...")
                # Try different approaches for content type handling
                try:
                    # Method 1: Try with content-type in options
                    result = bucket.upload(
                        unique_filename,
                        pdf_data,  # Binary data instead of file path
                        {"content-type": "application/pdf"}  # Explicit content type
                    )
                    logger.info("✓ Upload method 1 (with content-type) called successfully")
                except Exception as method1_error:
                    logger.warning(f"Method 1 failed: {str(method1_error)}")
                    try:
                        # Method 2: Try without content-type (rely on file extension)
                        result = bucket.upload(
                            unique_filename,
                            pdf_data  # Binary data without content-type
                        )
                        logger.info("✓ Upload method 2 (without content-type) called successfully")
                    except Exception as method2_error:
                        logger.error(f"Method 2 also failed: {str(method2_error)}")
                        # Method 3: Try with file path (fallback)
                        logger.info("Trying fallback method with file path...")
                        result = bucket.upload(
                            unique_filename,
                            pdf_path  # File path as fallback
                        )
                        logger.info("✓ Upload method 3 (file path fallback) called successfully")
                
                # If all methods fail, try direct REST API upload with proper headers
                if not result or (hasattr(result, 'error') and result.error):
                    logger.info("Trying direct REST API upload with proper headers...")
                    result = self._upload_via_rest_api(unique_filename, pdf_data, pdf_path)
                
                logger.info(f"Upload result type: {type(result)}")
                logger.info(f"Upload result: {result}")
                
            except Exception as upload_error:
                logger.error(f"Upload error details: {str(upload_error)}")
                logger.error(f"Upload error type: {type(upload_error)}")
                import traceback
                logger.error(f"Upload error traceback: {traceback.format_exc()}")
                raise upload_error
            
            # Check if upload was successful - handle different response formats
            if hasattr(result, 'error') and result.error:
                logger.error(f"Storage upload error: {result.error}")
                return None
            elif hasattr(result, 'data') and result.data:
                logger.info(f"Upload successful with data: {result.data}")
            else:
                logger.info(f"Upload completed with result: {result}")
            
            logger.info(f"PDF uploaded successfully: {unique_filename}")
            
            # Verify the uploaded file's content type
            try:
                logger.info("Verifying uploaded file content type...")
                file_info = bucket.get_public_url(unique_filename)
                logger.info(f"File public URL: {file_info}")
                
                # Try to get file metadata if available
                try:
                    file_list = bucket.list('', search=unique_filename)
                    if file_list and len(file_list) > 0:
                        for file_item in file_list:
                            if file_item.name == unique_filename:
                                logger.info(f"File metadata: {file_item}")
                                break
                except Exception as meta_error:
                    logger.warning(f"Could not get file metadata: {str(meta_error)}")
                
            except Exception as verify_error:
                logger.warning(f"Could not verify file content type: {str(verify_error)}")
            
            return unique_filename
            
        except Exception as e:
            logger.error(f"Error uploading PDF to storage: {str(e)}")
            return None
    
    def _upload_via_rest_api(self, filename: str, pdf_data: bytes, pdf_path: str) -> any:
        """
        Upload PDF via direct REST API call to ensure proper content type.
        
        Args:
            filename: Name for the file in storage
            pdf_data: Binary PDF data
            pdf_path: Original file path (fallback)
            
        Returns:
            Upload result or None if failed
        """
        try:
            import requests
            
            # Get the storage URL from Supabase client
            bucket = self.supabase.storage.from_('docs')
            
            # Construct the upload URL
            # This is a workaround for content-type issues with the Python client
            storage_url = f"{self.supabase.supabase_url}/storage/v1/object/docs/{filename}"
            
            # Prepare headers with proper content type
            headers = {
                'Authorization': f'Bearer {self.supabase.supabase_key}',
                'Content-Type': 'application/pdf',
                'x-upsert': 'true'  # Allow overwriting if file exists
            }
            
            logger.info(f"Uploading via REST API to: {storage_url}")
            logger.info(f"Headers: {headers}")
            
            # Upload the binary data
            response = requests.post(
                storage_url,
                data=pdf_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✓ REST API upload successful")
                return {"success": True, "data": response.json()}
            else:
                logger.error(f"REST API upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"REST API upload error: {str(e)}")
            return None
    
    def upload_rfq_data(self, pdf_path: str, solicitation_number: str) -> bool:
        """
        Upload RFQ PDF to Supabase storage (simplified version).
        
        Args:
            pdf_path: Path to the PDF file
            solicitation_number: Solicitation number for naming
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Upload PDF to storage
            storage_path = self.upload_pdf_to_storage(pdf_path, solicitation_number)
            if not storage_path:
                logger.error("Failed to upload PDF to storage")
                return False
            
            # Create signed URL for access
            signed_url_result = self.supabase.storage.from_('docs').create_signed_url(
                storage_path, 3600  # 1 hour expiry
            )
            
            logger.info(f"Signed URL result type: {type(signed_url_result)}")
            logger.info(f"Signed URL result: {signed_url_result}")
            
            if hasattr(signed_url_result, 'error') and signed_url_result.error:
                logger.error(f"Error creating signed URL: {signed_url_result.error}")
                return False
            
            logger.info(f"RFQ PDF uploaded successfully for {solicitation_number}")
            logger.info(f"Storage path: {storage_path}")
            
            # Handle different response formats for signed URL
            if hasattr(signed_url_result, 'data') and signed_url_result.data:
                signed_url = signed_url_result.data.get('signedUrl')
                logger.info(f"Signed URL created: {signed_url}")
            else:
                logger.info(f"Signed URL result: {signed_url_result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading RFQ PDF: {str(e)}")
            return False
    
    # Note: Database table operations removed to match UI behavior
    # The UI only uses Supabase storage, not database tables for documents
    
    def update_contract_amsc(self, contract_id: str, is_g_level: bool) -> bool:
        """
        Update the cde_g field in universal_contract_queue table.
        
        Args:
            contract_id: The contract ID to update
            is_g_level: Whether the AMSC code is G (True) or not (False)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            logger.info(f"Updating contract {contract_id} with cde_g: {is_g_level}")
            
            # Update the contract record
            result = self.supabase.table('universal_contract_queue').update({
                'cde_g': is_g_level
            }).eq('id', contract_id).execute()
            
            if result.error:
                logger.error(f"Error updating contract AMSC: {result.error}")
                return False
            
            logger.info(f"Successfully updated contract {contract_id} with cde_g: {is_g_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating contract AMSC: {str(e)}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
