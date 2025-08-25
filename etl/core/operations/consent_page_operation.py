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
            retry_attempts = inputs.get('retry_attempts', 3)
            base_url = inputs.get('base_url', 'https://www.dibbs.bsm.dla.mil')
            
            logger.info(f"🔄 CONSENT PAGE: Starting consent page handling for NSN: {nsn}")
            logger.info(f"🔄 CONSENT PAGE: Using base URL: {base_url}")
            logger.info(f"🔄 CONSENT PAGE: Timeout: {timeout}s, Retry attempts: {retry_attempts}")
            
            # Navigate to the NSN page
            nsn_url = f"{base_url}/RFQ/NSN/{nsn}"
            logger.info(f"🔄 CONSENT PAGE: Navigating to NSN URL: {nsn_url}")
            
            driver.get(nsn_url)
            logger.info(f"🔄 CONSENT PAGE: Page loaded, current URL: {driver.current_url}")
            
            # Wait for page to load
            time.sleep(2)
            logger.info(f"🔄 CONSENT PAGE: Waited 2 seconds for page load")
            
            # Check if we're on a consent page
            consent_elements = driver.find_elements(By.XPATH, "//input[@type='submit' and @value='I Agree']")
            logger.info(f"🔄 CONSENT PAGE: Found {len(consent_elements)} consent elements")
            
            if consent_elements:
                logger.info(f"🔄 CONSENT PAGE: Consent page detected, clicking 'I Agree'")
                consent_elements[0].click()
                logger.info(f"🔄 CONSENT PAGE: 'I Agree' clicked")
                
                # Wait for redirect
                time.sleep(3)
                logger.info(f"🔄 CONSENT PAGE: Waited 3 seconds after consent, current URL: {driver.current_url}")
                
                # Check if we're now on the actual NSN page
                if "NSN" in driver.current_url and nsn in driver.current_url:
                    logger.info(f"✅ CONSENT PAGE: Successfully passed consent page for NSN: {nsn}")
                    return OperationResult(
                        success=True,
                        status=OperationStatus.COMPLETED,
                        metadata={'nsn': nsn, 'consent_passed': True, 'final_url': driver.current_url}
                    )
                else:
                    logger.warning(f"⚠️ CONSENT PAGE: Consent passed but URL doesn't match expected NSN page")
                    logger.warning(f"⚠️ CONSENT PAGE: Expected NSN: {nsn}, Current URL: {driver.current_url}")
                    return OperationResult(
                        success=False,
                        status=OperationStatus.FAILED,
                        error=f"Consent passed but redirected to unexpected URL: {driver.current_url}"
                    )
            else:
                logger.info(f"✅ CONSENT PAGE: No consent page detected for NSN: {nsn}, proceeding directly")
                logger.info(f"✅ CONSENT PAGE: Current page title: {driver.title}")
                logger.info(f"✅ CONSENT PAGE: Current page source length: {len(driver.page_source)}")
                
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    metadata={'nsn': nsn, 'consent_passed': False, 'final_url': driver.current_url}
                )
                
        except Exception as e:
            logger.error(f"❌ CONSENT PAGE: Error handling consent page for NSN {nsn}: {str(e)}")
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"Consent page operation failed: {str(e)}"
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
