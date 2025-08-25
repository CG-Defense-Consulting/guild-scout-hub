"""
Closed Solicitation Check Operation

This operation checks if solicitations are closed by scanning HTML content
for specific text patterns. It can be reused by any operation that needs
to determine solicitation status.
"""

import logging
import re
from typing import Any, Dict, Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class ClosedSolicitationCheckOperation(BaseOperation):
    """
    Operation that checks if solicitations are closed.
    
    This operation:
    1. Scans HTML content for closed solicitation indicators
    2. Uses configurable text patterns for detection
    3. Can be reused by any operation that needs closed status checking
    """
    
    def __init__(self):
        """Initialize the closed solicitation check operation."""
        super().__init__(
            name="closed_solicitation_check",
            description="Check if solicitations are closed by scanning HTML content"
        )
        
        # Set required inputs
        self.set_required_inputs(['driver'])
        
        # Set optional inputs
        self.set_optional_inputs(['timeout', 'closed_patterns', 'open_patterns', 'wait_for_element'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the closed solicitation check operation.
        
        Args:
            inputs: Operation inputs containing 'driver' and optionally 'timeout', 'closed_patterns', 'open_patterns', 'wait_for_element'
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with closed status and detection details
        """
        try:
            driver = inputs['driver']
            timeout = inputs.get('timeout', 10)
            closed_patterns = inputs.get('closed_patterns', None)
            open_patterns = inputs.get('open_patterns', None)
            wait_for_element = inputs.get('wait_for_element', None)
            
            logger.info("Checking solicitation closed status...")
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    wait = WebDriverWait(driver, timeout)
                    wait.until(EC.presence_of_element_located((By.XPATH, wait_for_element)))
                    logger.info(f"Waited for element: {wait_for_element}")
                except TimeoutException:
                    logger.warning(f"Timeout waiting for element: {wait_for_element}")
            
            # Check for closed solicitations
            closed_status = self._check_closed_status(driver, closed_patterns, open_patterns)
            
            logger.info(f"Solicitation closed status: {closed_status}")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'is_closed': closed_status,
                    'status_determined': closed_status is not None
                },
                metadata={
                    'timeout_used': timeout,
                    'wait_for_element': wait_for_element,
                    'closed_patterns_used': closed_patterns,
                    'open_patterns_used': open_patterns
                }
            )
            
        except Exception as e:
            error_msg = f"Closed solicitation check operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def _check_closed_status(self, driver, closed_patterns: Optional[list] = None, 
                            open_patterns: Optional[list] = None) -> Optional[bool]:
        """
        Check if solicitations are closed by scanning HTML content.
        
        Args:
            driver: Selenium WebDriver instance
            closed_patterns: Optional custom patterns for closed solicitations
            open_patterns: Optional custom patterns for open solicitations
            
        Returns:
            True if closed, False if open, None if unknown
        """
        try:
            page_source = driver.page_source
            
            # Use default patterns if none provided
            if closed_patterns is None:
                closed_patterns = [
                    r"No record of National Stock Number: \w+ with open DIBBS Request For Quotes \(RFQ\) solicitations\.",
                    r"No open solicitations found",
                    r"Solicitation is closed",
                    r"Request for Quote is closed",
                    r"RFQ is closed",
                    r"No active solicitations",
                    r"All solicitations are closed"
                ]
            
            # if open_patterns is None:
            #     open_patterns = [
            #         r"Open solicitations found",
            #         r"Active solicitations",
            #         r"Request for Quote is open",
            #         r"RFQ is open",
            #         r"Open RFQ solicitations"
            #     ]
            
            # Check for closed patterns
            for pattern in closed_patterns:
                if re.search(pattern, page_source, re.IGNORECASE):
                    logger.info(f"Closed solicitation detected with pattern: {pattern}")
                    return True
            
            # # Check for open patterns
            # for pattern in open_patterns:
            #     if re.search(pattern, page_source, re.IGNORECASE):
            #         logger.info(f"Open solicitation detected with pattern: {pattern}")
            #         return False
            
            # Also check for specific NSN closed message (common case)
            nsn_closed_pattern = r"No record of National Stock Number: (\w+) with open DIBBS Request For Quotes \(RFQ\) solicitations\."
            nsn_match = re.search(nsn_closed_pattern, page_source, re.IGNORECASE)
            if nsn_match:
                nsn = nsn_match.group(1)
                logger.info(f"NSN {nsn} has closed solicitations")
                return True
            
            # Check for common closed indicators in the DOM
            closed_indicators = [
                "//*[contains(text(), 'closed')]",
                "//*[contains(text(), 'Closed')]",
                "//*[contains(text(), 'no open solicitations')]",
                "//*[contains(text(), 'No open solicitations')]"
            ]
            
            for indicator in closed_indicators:
                try:
                    elements = driver.find_elements(By.XPATH, indicator)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if any(pattern.lower() in text.lower() for pattern in ['closed', 'no open']):
                                logger.info(f"Closed indicator found in DOM: {text}")
                                return True
                except:
                    continue
            
            # # Check for common open indicators in the DOM
            # open_indicators = [
            #     "//*[contains(text(), 'open')]",
            #     "//*[contains(text(), 'Open')]",
            #     "//*[contains(text(), 'active')]",
            #     "//*[contains(text(), 'Active')]"
            # ]
            
            # for indicator in open_indicators:
            #     try:
            #         elements = driver.find_elements(By.XPATH, indicator)
            #         for element in elements:
            #             if element.is_displayed():
            #                 text = element.text.strip()
            #                 if any(pattern.lower() in text.lower() for pattern in ['open', 'active']):
            #                     logger.info(f"Open indicator found in DOM: {text}")
            #                     return False
            #     except:
            #         continue
            
            # If we can't determine status, return None
            logger.warning("Could not determine solicitation closed status")
            return None
            
        except Exception as e:
            logger.warning(f"Error checking closed status: {str(e)}")
            return None
    
    def can_apply_to_batch(self) -> bool:
        """
        Closed solicitation check can be applied to batches.
        
        Returns:
            True - this operation supports batch processing
        """
        return True
    
    def apply_to_batch(self, items: list, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> list:
        """
        Apply closed solicitation check to a batch of items.
        
        Args:
            items: List of items to check (could be NSNs, URLs, etc.)
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each item
        """
        if context is None:
            context = {}
        
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} items for closed solicitation check")
        
        for i, item in enumerate(items, 1):
            logger.info(f"Processing item {i}/{total_items}")
            
            # Create item-specific inputs
            item_inputs = inputs.copy()
            item_inputs['item'] = item
            
            # Execute operation for this item
            result = self.execute(item_inputs, context)
            results.append(result)
        
        logger.info(f"Batch processing completed. {len([r for r in results if r.success])}/{total_items} successful")
        return results
