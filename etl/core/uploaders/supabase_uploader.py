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
            # Get environment variables
            supabase_url = os.getenv('VITE_SUPABASE_URL')
            supabase_key = os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.error("Missing Supabase environment variables")
                raise ValueError("Missing Supabase environment variables")
            
            # Create client
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
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
            
            # Create unique filename using the same format as UI
            timestamp = self._get_timestamp().replace(':', '-').replace('.', '-')
            file_extension = Path(pdf_path).suffix
            
            # Format: rfq-{solicitation_number}-{timestamp}-{original_name}.{extension}
            # This matches the UI format: contract-{contractId}-{timestamp}-{encodedOriginalName}.{extension}
            unique_filename = f"rfq-{solicitation_number}-{timestamp}-{Path(pdf_path).stem}{file_extension}"
            
            # Upload to Supabase storage using the same approach as UI
            logger.info(f"Uploading PDF to storage: {unique_filename}")
            
            # Open and upload the file directly (same as UI)
            with open(pdf_path, 'rb') as file:
                result = self.supabase.storage.from_('docs').upload(
                    unique_filename,
                    file,  # Pass the file object directly, not bytes
                    {
                        'cacheControl': '3600',
                        'upsert': False
                    }
                )
            
            if result.error:
                logger.error(f"Storage upload error: {result.error}")
                return None
            
            logger.info(f"PDF uploaded successfully: {unique_filename}")
            return unique_filename
            
        except Exception as e:
            logger.error(f"Error uploading PDF to storage: {str(e)}")
            return None
    
    def upload_rfq_data(self, rfq_data: Dict[str, Any]) -> bool:
        """
        Upload RFQ data to Supabase using the same approach as the UI.
        
        Args:
            rfq_data: RFQ data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Debug: log the incoming data
            logger.info(f"Uploading RFQ data: {list(rfq_data.keys())}")
            logger.info(f"PDF path: {rfq_data.get('pdf_path')}")
            
            # Extract data
            solicitation_number = rfq_data.get('solicitation_number')
            pdf_path = rfq_data.get('pdf_path')
            
            if not solicitation_number or not pdf_path:
                logger.error("Missing required RFQ data")
                return False
            
            # Upload PDF to storage first (same as UI)
            storage_path = self.upload_pdf_to_storage(pdf_path, solicitation_number)
            if not storage_path:
                logger.error("Failed to upload PDF to storage")
                return False
            
            # Create signed URL (same as UI)
            signed_url_result = self.supabase.storage.from_('docs').create_signed_url(
                storage_path, 3600  # 1 hour expiry
            )
            
            if signed_url_result.error:
                logger.error(f"Error creating signed URL: {signed_url_result.error}")
                return False
            
            logger.info(f"RFQ PDF uploaded successfully for {solicitation_number}")
            logger.info(f"Storage path: {storage_path}")
            logger.info(f"Signed URL created: {signed_url_result.data.get('signedUrl')}")
            
            # Note: We're not inserting into a database table like the UI
            # The UI just stores files in the 'docs' bucket and accesses them via storage API
            # This matches the existing UI behavior exactly
            
            return True
            
        except Exception as e:
            logger.error(f"Error uploading RFQ data: {str(e)}")
            return False
    
    # Note: Database table operations removed to match UI behavior
    # The UI only uses Supabase storage, not database tables for documents
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
