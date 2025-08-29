"""
Consent Page Operation

This operation handles DLA consent pages that commonly appear when accessing DIBBS.
It can be reused by any operation that needs to navigate through consent pages.
"""

import logging
from typing import Any, Dict, Optional
from selenium.webdriver.common.by import By

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class ConsentPageOperation(BaseOperation):
    """
    Operation that handles DLA consent pages.
    
    This operation:
    1. Detects if a consent page is present
    2. Clicks the appropriate consent button
    3. Can be reused by any operation that needs to consent handling
    """
    
    def __init__(self):
        """Initialize the consent page operation."""
        super().__init__(
            name="consent_page",
            description="Handle DLA consent pages by clicking appropriate consent buttons"
        )
        
        # Set required inputs - NSN is optional now
        self.set_required_inputs([])
        
        # Set optional inputs
        self.set_optional_inputs(['nsn', 'timeout', 'retry_attempts', 'base_url', 'handle_current_page'])
    
    def _check_page_changed(self, driver, original_url: str, original_title: str, original_source_length: int) -> bool:
        """
        Check if the page changed after clicking consent button.
        
        Args:
            driver: Selenium WebDriver instance
            original_url: URL before clicking consent button
            original_title: Page title before clicking consent button
            original_source_length: Length of page source before clicking consent button
            
        Returns:
            True if page changed significantly, False otherwise
        """
        try:
            current_url = driver.current_url
            current_title = driver.title
            current_source_length = len(driver.page_source)
            
            # Check if URL changed
            if current_url != original_url:
                logger.info(f"Page URL changed: {original_url} -> {current_url}")
                return True
            
            # Check if title changed
            if current_title != original_title:
                logger.info(f"Page title changed: {original_title} -> {current_title}")
                return True
            
            # Check if page source changed significantly (more than 10% difference)
            source_diff = abs(current_source_length - original_source_length)
            if source_diff > (original_source_length * 0.1):
                logger.info(f"Page source changed significantly: {original_source_length} -> {current_source_length} chars")
                return True
            
            # Check if we're no longer on a consent page
            page_source = driver.page_source
            if 'Department of Defense' not in page_source and 'Notice and Consent' not in page_source:
                logger.info("Consent page content no longer present")
                return True
            
            logger.warning("Page did not change after clicking consent button")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking page change: {str(e)}")
            return False
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the consent page operation.
        
        Args:
            inputs: Operation inputs
            context: Shared context (should contain chrome_driver)
            
        Returns:
            OperationResult with success status and metadata
        """
        try:
            driver = context.get('chrome_driver')
            if not driver:
                return OperationResult(
                    success=False, 
                    status=OperationStatus.FAILED, 
                    error="Chrome driver not found in context."
                )
            
            nsn = inputs.get('nsn')
            timeout = inputs.get('timeout', 30)
            base_url = inputs.get('base_url', 'https://www.dibbs.bsm.dla.mil')
            handle_current_page = inputs.get('handle_current_page', True)
            
            # If NSN is provided and we're not handling current page, navigate to NSN page
            if nsn and not handle_current_page:
                nsn_url = f"{base_url}/rfq/rfqnsn.aspx?value={nsn}"
                driver.get(nsn_url)
                import time
                time.sleep(1)
            
            # Capture page state before clicking consent button
            original_url = driver.current_url
            original_title = driver.title
            original_source_length = len(driver.page_source)
            
            # Look for consent button and click it
            consent_selectors = [
                "//input[@type='submit' and @value='OK']"
            ]
            
            for selector in consent_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"Found consent button: {selector}")
                        elements[0].click()
                        
                        # Wait for page to process
                        import time
                        time.sleep(1)
                        
                        # Check if page changed
                        if self._check_page_changed(driver, original_url, original_title, original_source_length):
                            logger.info("Consent button click successful - page changed")
                            return OperationResult(
                                success=True,
                                status=OperationStatus.COMPLETED,
                                metadata={'nsn': nsn, 'consent_passed': True, 'final_url': driver.current_url}
                            )
                        else:
                            logger.error("Consent button click failed - page did not change")
                            return OperationResult(
                                success=False,
                                status=OperationStatus.FAILED,
                                error="Consent button clicked but page did not change"
                            )
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
                    continue
            
            # No consent page found
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                metadata={'nsn': nsn, 'consent_passed': False, 'final_url': driver.current_url}
            )
                
        except Exception as e:
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"Consent page operation failed: {str(e)}"
            )
