"""
Consent Page Operation

This operation handles DLA consent pages that commonly appear when accessing DIBBS.
It can be reused by any operation that needs to navigate through consent pages.
"""

import logging
from typing import Any, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class ConsentPageOperation(BaseOperation):
    """
    Operation that handles DLA consent pages.
    
    This operation:
    1. Detects if a consent page is present
    2. Clicks the appropriate consent button
    3. Can be reused by any operation that needs consent handling
    """
    
    def __init__(self):
        """Initialize the consent page operation."""
        super().__init__(
            name="consent_page",
            description="Handle DLA consent pages by clicking appropriate consent buttons"
        )
        
        # Set required inputs
        self.set_required_inputs(['driver'])
        
        # Set optional inputs
        self.set_optional_inputs(['timeout', 'consent_selectors', 'url'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the consent page operation.
        
        Args:
            inputs: Operation inputs containing 'driver' and optionally 'timeout', 'consent_selectors', 'url'
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with consent handling success status
        """
        try:
            driver = inputs['driver']
            timeout = inputs.get('timeout', 10)
            consent_selectors = inputs.get('consent_selectors', None)
            url = inputs.get('url', None)
            
            logger.info("Checking for consent page...")
            
            # If URL provided, navigate to it first
            if url:
                logger.info(f"Navigating to: {url}")
                driver.get(url)
            
            # Handle consent page
            consent_handled = self._handle_consent_page(driver, timeout, consent_selectors)
            
            if consent_handled:
                logger.info("Consent page handled successfully")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={
                        'consent_handled': True,
                        'consent_detected': True
                    },
                    metadata={
                        'timeout_used': timeout,
                        'url_processed': url
                    }
                )
            else:
                logger.info("No consent page detected or consent not required")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={
                        'consent_handled': False,
                        'consent_detected': False
                    },
                    metadata={
                        'timeout_used': timeout,
                        'url_processed': url
                    }
                )
                
        except Exception as e:
            error_msg = f"Consent page operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def _handle_consent_page(self, driver, timeout: int, custom_selectors: Optional[list] = None) -> bool:
        """
        Handle DLA consent page if it appears.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Timeout for consent page operations
            custom_selectors: Optional custom selectors for consent buttons
            
        Returns:
            True if consent handled successfully, False if no consent page found
        """
        try:
            wait = WebDriverWait(driver, timeout)
            
            # Use custom selectors if provided, otherwise use defaults
            if custom_selectors:
                consent_selectors = custom_selectors
            else:
                consent_selectors = [
                    "//button[contains(text(), 'Ok')]",
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'I Accept')]",
                    "//button[contains(text(), 'I Agree')]",
                    "//input[@type='submit' and contains(@value, 'Ok')]",
                    "//input[@type='submit' and contains(@value, 'OK')]",
                    "//input[@type='submit' and contains(@value, 'Accept')]",
                    "//input[@type='submit' and contains(@value, 'I Accept')]",
                    "//input[@type='submit' and contains(@value, 'I Agree')]",
                    "//a[contains(text(), 'Ok')]",
                    "//a[contains(text(), 'OK')]",
                    "//a[contains(text(), 'Accept')]"
                ]
            
            # Check for consent page indicators
            consent_indicators = [
                "//*[contains(text(), 'consent')]",
                "//*[contains(text(), 'Consent')]",
                "//*[contains(text(), 'accept')]",
                "//*[contains(text(), 'Accept')]",
                "//*[contains(text(), 'agree')]",
                "//*[contains(text(), 'Agree')]"
            ]
            
            # First, check if we're on a consent page
            consent_page_detected = False
            for indicator in consent_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        consent_page_detected = True
                        logger.info(f"Consent page detected with indicator: {indicator}")
                        break
                except:
                    continue
            
            # If no consent page detected, return False
            if not consent_page_detected:
                return False
            
            # Try to find and click consent button
            for selector in consent_selectors:
                try:
                    consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    logger.info(f"Found consent button using selector: {selector}")
                    
                    # Click the consent button
                    consent_button.click()
                    logger.info("Consent button clicked successfully")
                    
                    # Wait a moment for the page to process
                    import time
                    time.sleep(1)
                    
                    return True
                    
                except TimeoutException:
                    continue
            
            # If we get here, we detected a consent page but couldn't handle it
            logger.warning("Consent page detected but no consent button found")
            return False
            
        except Exception as e:
            logger.warning(f"Error handling consent page: {str(e)}")
            return False
    
    def can_apply_to_batch(self) -> bool:
        """
        Consent page operation can be applied to batches.
        
        Returns:
            True - this operation supports batch processing
        """
        return True
    
    def apply_to_batch(self, items: list, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> list:
        """
        Apply consent page handling to a batch of URLs or pages.
        
        Args:
            items: List of URLs or page identifiers to process
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each item
        """
        if context is None:
            context = {}
        
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} items for consent page handling")
        
        for i, item in enumerate(items, 1):
            logger.info(f"Processing item {i}/{total_items}")
            
            # Create item-specific inputs
            item_inputs = inputs.copy()
            if isinstance(item, str) and item.startswith('http'):
                item_inputs['url'] = item
            else:
                item_inputs['item'] = item
            
            # Execute operation for this item
            result = self.execute(item_inputs, context)
            results.append(result)
        
        logger.info(f"Batch processing completed. {len([r for r in results if r.success])}/{total_items} successful")
        return results
