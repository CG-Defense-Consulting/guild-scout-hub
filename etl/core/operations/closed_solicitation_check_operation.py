#!/usr/bin/env python3
"""
Closed Solicitation Check Operation

This operation focuses purely on checking if a solicitation is closed from HTML content.
It assumes the HTML content is already provided and only checks for closed status indicators.
"""

import logging
import re
from typing import Dict, Any, Optional
from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class ClosedSolicitationCheckOperation(BaseOperation):
    """
    Operation to check if a solicitation is closed from HTML content.
    
    This operation:
    - Takes HTML content as input
    - Checks for closed solicitation indicators
    - Returns True if closed, False if open, None if unknown
    - Does NOT handle navigation, driver setup, or page loading
    """
    
    def __init__(self):
        super().__init__(
            name="closed_solicitation_check", 
            description="Check if solicitation is closed from HTML content"
        )
        self.set_required_inputs(['html_content'])
        self.set_optional_inputs(['nsn'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the closed solicitation check operation.
        
        Args:
            inputs: Operation inputs containing 'html_content' and optional 'nsn' for logging
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with closed status information
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
            
            logger.info(f"🔍 CLOSED CHECK: Starting closed solicitation check for NSN: {nsn}")
            logger.info(f"🔍 CLOSED CHECK: HTML content length: {len(html_content)} characters")
            
            # Check for closed solicitation status
            closed_status = self._check_closed_solicitation_status(html_content, nsn)
            
            logger.info(f"🔍 CLOSED CHECK: Closed status check result for NSN {nsn}: {closed_status}")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={'is_closed': closed_status, 'nsn': nsn},
                metadata={'check_method': 'html_parsing'}
            )
                
        except Exception as e:
            logger.error(f"❌ CLOSED CHECK: Error checking closed status for NSN {nsn}: {str(e)}")
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"Closed solicitation check operation failed: {str(e)}"
            )

    def _check_closed_solicitation_status(self, html_content: str, nsn: str) -> Optional[bool]:
        """
        Check if the solicitation is closed by looking for specific text patterns.
        
        This method checks for the specific language mentioned in the business logic:
        "No record of National Stock Number: {NSN} with open DIBBS Request For Quotes (RFQ) solicitations."
        
        Args:
            html_content: HTML content to analyze
            nsn: National Stock Number for logging
            
        Returns:
            True if closed, False if open, None if unknown
        """
        try:
            # Look for the specific closed solicitation pattern
            closed_pattern = f"No record of National Stock Number: {nsn} with open DIBBS Request For Quotes (RFQ) solicitations."
            
            if closed_pattern in html_content:
                logger.info(f"🔍 CLOSED CHECK: NSN {nsn}: Closed solicitation detected via specific pattern")
                return True
            
            # Look for other indicators of closed solicitations
            closed_indicators = [
                "no open solicitations",
                "no open RFQ solicitations", 
                "no open DIBBS solicitations",
                "solicitation closed",
                "no active solicitations"
            ]
            
            for indicator in closed_indicators:
                if indicator.lower() in html_content.lower():
                    logger.info(f"🔍 CLOSED CHECK: NSN {nsn}: Closed solicitation detected via indicator: {indicator}")
                    return True
            
            # If we can't determine, return None (unknown)
            logger.info(f"🔍 CLOSED CHECK: NSN {nsn}: Solicitation status could not be determined")
            return None
            
        except Exception as e:
            logger.error(f"❌ CLOSED CHECK: Error checking closed solicitation status for NSN {nsn}: {str(e)}")
            return None

    def can_apply_to_batch(self) -> bool:
        """This operation can be applied to batches of HTML content."""
        return True

    def apply_to_batch(self, items: list, inputs: Dict[str, Any], 
                      context: Dict[str, Any]) -> list:
        """
        Apply closed solicitation check to a batch of HTML content items.
        
        Args:
            items: List of HTML content items to process
            inputs: Operation inputs
            context: Shared workflow context
            
        Returns:
            List of OperationResult objects for each HTML content item
        """
        results = []
        total_items = len(items)
        
        logger.info(f"🔍 CLOSED CHECK: Processing batch of {total_items} HTML content items")
        
        for i, html_content in enumerate(items):
            logger.info(f"🔍 CLOSED CHECK: Processing item {i+1}/{total_items}")
            
            # Create inputs for this specific HTML content
            item_inputs = inputs.copy()
            item_inputs['html_content'] = html_content
            
            # Execute check for this HTML content
            result = self._execute(item_inputs, context)
            results.append(result)
        
        # Log batch completion
        successful = len([r for r in results if r.success])
        logger.info(f"🔍 CLOSED CHECK: Batch processing completed. {successful}/{total_items} successful")
        return results
