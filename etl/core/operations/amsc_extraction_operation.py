#!/usr/bin/env python3
"""
AMSC Extraction Operation

This operation focuses purely on extracting AMSC codes from HTML content.
It assumes the HTML content is already provided and only extracts the AMSC code.
"""

import logging
import re
from typing import Dict, Any, Optional
from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class AmscExtractionOperation(BaseOperation):
    """
    Operation to extract AMSC codes from HTML content.
    
    This operation:
    - Takes HTML content as input
    - Extracts AMSC code using various selectors and patterns
    - Returns the AMSC code or None if not found
    - Does NOT handle navigation, driver setup, or page loading
    """
    
    def __init__(self):
        super().__init__(
            name="amsc_extraction", 
            description="Extract AMSC codes from HTML content"
        )
        self.set_required_inputs(['html_content'])
        self.set_optional_inputs(['nsn'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the AMSC extraction operation.
        
        Args:
            inputs: Operation inputs containing 'html_content' and optional 'nsn' for logging
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with extracted AMSC code or error information
        """
        try:
            html_content = inputs.get('html_content')
            nsn = inputs.get('nsn', 'unknown')
            
            if not html_content:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required input: 'html_content'"
                )
            
            logger.info(f"🔍 AMSC EXTRACTION: Starting AMSC extraction for NSN: {nsn}")
            logger.info(f"🔍 AMSC EXTRACTION: HTML content length: {len(html_content)} characters")
            
            # Extract AMSC code from HTML content
            amsc_code = self._extract_amsc_from_html(html_content, nsn)
            
            if amsc_code:
                logger.info(f"✅ AMSC EXTRACTION: Successfully extracted AMSC code for NSN {nsn}: {amsc_code}")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={'amsc_code': amsc_code, 'nsn': nsn},
                    metadata={'extraction_method': 'html_parsing'}
                )
            else:
                logger.warning(f"⚠️ AMSC EXTRACTION: No AMSC code found for NSN {nsn}")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={'amsc_code': None, 'nsn': nsn},
                    metadata={'extraction_method': 'none_found'}
                )
                
        except Exception as e:
            logger.error(f"❌ AMSC EXTRACTION: Error extracting AMSC code for NSN {nsn}: {str(e)}")
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"AMSC extraction operation failed: {str(e)}"
            )

    def _extract_amsc_from_html(self, html_content: str, nsn: str) -> Optional[str]:
        """
        Extract AMSC code from HTML content using various methods.
        
        Args:
            html_content: HTML content to parse
            nsn: National Stock Number for logging
            
        Returns:
            AMSC code string or None if not found
        """
        try:
            # Method 1: Look for DIBBS legend pattern with strong tags
            # Pattern: <legend>...AMSC: <strong>T</strong>...</legend>
            legend_pattern = r'<legend[^>]*>.*?AMSC:\s*<strong>([A-Z])\s*</strong>'
            match = re.search(legend_pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                amsc_code = match.group(1).upper()
                logger.info(f"🔍 AMSC EXTRACTION: AMSC code found via legend pattern for NSN {nsn}: {amsc_code}")
                return amsc_code
            
            # Method 2: Look for AMSC: X pattern in text
            amsc_pattern = r'AMSC:\s*([A-Z])\s*'
            match = re.search(amsc_pattern, html_content, re.IGNORECASE)
            if match:
                amsc_code = match.group(1).upper()
                logger.info(f"🔍 AMSC EXTRACTION: AMSC code found via AMSC pattern for NSN {nsn}: {amsc_code}")
                return amsc_code
            
            # Method 3: Look for DIBBS specific full legend pattern
            # Pattern: NSN: XXXX Nomenclature: XXX AMSC: X
            dibbs_pattern = r'NSN:[^A]*Nomenclature:[^A]*AMSC:\s*([A-Z])'
            match = re.search(dibbs_pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                amsc_code = match.group(1).upper()
                logger.info(f"🔍 AMSC EXTRACTION: AMSC code found via DIBBS pattern for NSN {nsn}: {amsc_code}")
                return amsc_code
            
            # Method 4: Look for any AMSC code pattern
            general_pattern = r'AMSC[:\s]+([A-Z])'
            match = re.search(general_pattern, html_content, re.IGNORECASE)
            if match:
                amsc_code = match.group(1).upper()
                logger.info(f"🔍 AMSC EXTRACTION: AMSC code found via general pattern for NSN {nsn}: {amsc_code}")
                return amsc_code
            
            logger.warning(f"⚠️ AMSC EXTRACTION: No AMSC code patterns found in HTML for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"❌ AMSC EXTRACTION: Error in HTML parsing for NSN {nsn}: {str(e)}")
            return None

    def can_apply_to_batch(self) -> bool:
        """This operation can be applied to batches of HTML content."""
        return True

    def apply_to_batch(self, items: list, inputs: Dict[str, Any], 
                      context: Dict[str, Any]) -> list:
        """
        Apply AMSC extraction to a batch of HTML content items.
        
        Args:
            items: List of HTML content items to process
            inputs: Operation inputs
            context: Shared workflow context
            
        Returns:
            List of OperationResult objects for each HTML content item
        """
        results = []
        total_items = len(items)
        
        logger.info(f"🔍 AMSC EXTRACTION: Processing batch of {total_items} HTML content items")
        
        for i, html_content in enumerate(items):
            logger.info(f"🔍 AMSC EXTRACTION: Processing item {i+1}/{total_items}")
            
            # Create inputs for this specific HTML content
            item_inputs = inputs.copy()
            item_inputs['html_content'] = html_content
            
            # Execute extraction for this HTML content
            result = self._execute(item_inputs, context)
            results.append(result)
        
        # Log batch completion
        successful = len([r for r in results if r.success])
        logger.info(f"🔍 AMSC EXTRACTION: Batch processing completed. {successful}/{total_items} successful")
        return results
