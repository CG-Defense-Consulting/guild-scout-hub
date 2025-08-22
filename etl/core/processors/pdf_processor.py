"""
PDF Processor
Handles PDF parsing and data extraction
"""

from typing import Dict, Any, Optional
import logging
import re
from pathlib import Path
import PyPDF2
import pdfplumber

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processes PDF files to extract structured data."""
    
    def __init__(self):
        """Initialize the PDF processor."""
        # TODO: Initialize PDF processing libraries
        pass
        
    def extract_rfq_data(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract RFQ data from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted data dictionary or None if failed
        """
        try:
            logger.info(f"Extracting RFQ data from: {pdf_path}")
            
            if not Path(pdf_path).exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            # Extract text using pdfplumber (more reliable for complex PDFs)
            text_content = self._extract_text_with_pdfplumber(pdf_path)
            
            if not text_content:
                logger.warning("No text content extracted from PDF")
                return None
            
            # Parse the extracted text
            parsed_data = self._parse_rfq_text(text_content)
            
            # Add file metadata
            parsed_data.update({
                'pdf_path': pdf_path,
                'file_size': Path(pdf_path).stat().st_size,
                'extraction_timestamp': self._get_timestamp()
            })
            
            logger.info(f"Successfully extracted RFQ data from {pdf_path}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error extracting RFQ data from {pdf_path}: {str(e)}")
            return None
    
    def _extract_text_with_pdfplumber(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- PAGE {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
            
            if text_content:
                return "\n".join(text_content)
            else:
                logger.warning("No text content extracted from any page")
                return None
                
        except Exception as e:
            logger.error(f"Error using pdfplumber: {str(e)}")
            # Fallback to PyPDF2
            return self._extract_text_with_pypdf2(pdf_path)
    
    def _extract_text_with_pypdf2(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from PDF using PyPDF2 (fallback method).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            text_content = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(f"--- PAGE {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
            
            if text_content:
                return "\n".join(text_content)
            else:
                logger.warning("No text content extracted from any page")
                return None
                
        except Exception as e:
            logger.error(f"Error using PyPDF2: {str(e)}")
            return None
    
    def _parse_rfq_text(self, text_content: str) -> Dict[str, Any]:
        """
        Parse extracted text to identify RFQ data.
        
        Args:
            text_content: Raw text content from PDF
            
        Returns:
            Parsed RFQ data dictionary
        """
        parsed_data = {
            'solicitation_number': None,
            'title': None,
            'agency': None,
            'date_posted': None,
            'due_date': None,
            'contact_info': None,
            'description': None,
            'requirements': [],
            'raw_text': text_content[:1000]  # Store first 1000 chars for debugging
        }
        
        try:
            # Extract solicitation number (common patterns)
            solicitation_patterns = [
                r'Solicitation\s+Number[:\s]+([A-Z0-9-]+)',
                r'RFQ[:\s]+([A-Z0-9-]+)',
                r'Request\s+for\s+Quote[:\s]+([A-Z0-9-]+)',
                r'([A-Z]{2,3}-\d{4}-\d{4})',  # Common format: XX-YYYY-XXXX
                r'([A-Z]{2,3}\d{4}-\d{4})',   # Common format: XXYYYY-XXXX
            ]
            
            for pattern in solicitation_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    parsed_data['solicitation_number'] = match.group(1).strip()
                    break
            
            # Extract title (usually in first few lines)
            lines = text_content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and len(line) > 10 and not line.startswith('---'):
                    # Skip page headers and very short lines
                    if not re.match(r'^[A-Z\s]+$', line):  # Not all caps
                        parsed_data['title'] = line[:200]  # Limit length
                        break
            
            # Extract agency information
            agency_patterns = [
                r'Defense\s+Logistics\s+Agency',
                r'DLA',
                r'Department\s+of\s+Defense',
                r'DoD'
            ]
            
            for pattern in agency_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    parsed_data['agency'] = match.group(0)
                    break
            
            # Extract dates
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
                r'(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
                r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
            ]
            
            dates_found = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text_content)
                dates_found.extend(matches)
            
            if dates_found:
                parsed_data['date_posted'] = dates_found[0]  # First date found
                if len(dates_found) > 1:
                    parsed_data['due_date'] = dates_found[1]  # Second date might be due date
            
            # Extract contact information
            contact_patterns = [
                r'Contact[:\s]+([^\n]+)',
                r'Phone[:\s]+([^\n]+)',
                r'Email[:\s]+([^\n]+)',
                r'Point\s+of\s+Contact[:\s]+([^\n]+)'
            ]
            
            contact_info = []
            for pattern in contact_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    contact_info.append(match.group(1).strip())
            
            if contact_info:
                parsed_data['contact_info'] = '; '.join(contact_info)
            
            # Extract description (look for longer paragraphs)
            paragraphs = text_content.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if len(para) > 50 and not para.startswith('---'):
                    # Skip page headers and short paragraphs
                    if not re.match(r'^[A-Z\s]+$', para):  # Not all caps
                        parsed_data['description'] = para[:500]  # Limit length
                        break
            
            logger.info(f"Parsed RFQ data: {parsed_data['solicitation_number']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing RFQ text: {str(e)}")
            return parsed_data
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
