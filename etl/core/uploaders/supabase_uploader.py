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
        Upload PDF to Supabase storage bucket.
        
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
            
            # Create unique filename
            timestamp = self._get_timestamp()
            file_extension = Path(pdf_path).suffix
            original_name = Path(pdf_path).stem
            
            # Format: rfq-{solicitation_number}-{timestamp}-{original_name}.{extension}
            unique_filename = f"rfq-{solicitation_number}-{timestamp}-{original_name}{file_extension}"
            
            # Read file content
            with open(pdf_path, 'rb') as file:
                file_content = file.read()
            
            # Upload to Supabase storage
            logger.info(f"Uploading PDF to storage: {unique_filename}")
            result = self.supabase.storage.from_('docs').upload(
                unique_filename,
                file_content,
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
        Upload RFQ data to Supabase.
        
        Args:
            rfq_data: RFQ data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Extract data
            solicitation_number = rfq_data.get('solicitation_number')
            pdf_path = rfq_data.get('pdf_path')
            
            if not solicitation_number or not pdf_path:
                logger.error("Missing required RFQ data")
                return False
            
            # Upload PDF to storage first
            storage_path = self.upload_pdf_to_storage(pdf_path, solicitation_number)
            if not storage_path:
                logger.error("Failed to upload PDF to storage")
                return False
            
            # Create signed URL
            signed_url_result = self.supabase.storage.from_('docs').create_signed_url(
                storage_path, 3600  # 1 hour expiry
            )
            
            if signed_url_result.error:
                logger.error(f"Error creating signed URL: {signed_url_result.error}")
                return False
            
            # Prepare data for database
            db_data = {
                'solicitation_number': solicitation_number,
                'title': rfq_data.get('title', ''),
                'pdf_path': storage_path,
                'public_url': signed_url_result.data.get('signedUrl'),
                'uploaded_at': self._get_timestamp(),
                'status': 'uploaded'
            }
            
            # Upload to database (assuming you have an rfq_documents table)
            # You may need to adjust the table name and structure
            result = self.supabase.table('rfq_documents').insert(db_data).execute()
            
            if result.error:
                logger.error(f"Database upload error: {result.error}")
                return False
            
            logger.info(f"RFQ data uploaded successfully for {solicitation_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading RFQ data: {str(e)}")
            return False
    
    def upload_solicitation_index(self, index_data: Dict[str, Any]) -> bool:
        """
        Upload solicitation index data to Supabase.
        
        Args:
            index_data: Solicitation index data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Add timestamp
            index_data['created_at'] = self._get_timestamp()
            
            # Upload to database (assuming you have an rfq_index_extract table)
            result = self.supabase.table('rfq_index_extract').insert(index_data).execute()
            
            if result.error:
                logger.error(f"Database upload error: {result.error}")
                return False
            
            logger.info("Solicitation index uploaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading solicitation index: {str(e)}")
            return False
    
    def upload_award_history(self, award_data: Dict[str, Any]) -> bool:
        """
        Upload award history data to Supabase.
        
        Args:
            award_data: Award history data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Add timestamp
            award_data['created_at'] = self._get_timestamp()
            
            # Upload to database (assuming you have an award_history table)
            result = self.supabase.table('award_history').insert(award_data).execute()
            
            if result.error:
                logger.error(f"Database upload error: {result.error}")
                return False
            
            logger.info("Award history uploaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading award history: {str(e)}")
            return False
    
    def check_award_history_exists(self, solicitation_number: str) -> bool:
        """
        Check if award history already exists for a solicitation.
        
        Args:
            solicitation_number: The solicitation number to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            if not self.supabase:
                logger.error("Supabase client not initialized")
                return False
            
            # Query database (assuming you have an award_history table)
            result = self.supabase.table('award_history').select(
                'id'
            ).eq('solicitation_number', solicitation_number).limit(1).execute()
            
            if result.error:
                logger.error(f"Database query error: {result.error}")
                return False
            
            exists = len(result.data) > 0
            logger.info(f"Award history exists for {solicitation_number}: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking award history existence: {str(e)}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
