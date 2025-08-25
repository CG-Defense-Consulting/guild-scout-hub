"""
AMSC Extraction Operation

This operation extracts AMSC codes from NSN details pages using the shared Chrome driver.
It can be applied to individual NSNs or batched over multiple NSNs.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class AmscExtractionOperation(BaseOperation):
    """
    Operation that extracts AMSC codes from NSN details pages.
    
    This operation:
    1. Uses the shared Chrome driver from context
    2. Navigates to NSN details pages
    3. Handles consent pages
    4. Extracts AMSC codes
    5. Checks for closed solicitations
    6. Can be applied to batches of NSNs
    """
    
    def __init__(self):
        """Initialize the AMSC extraction operation."""
        super().__init__(
            name="amsc_extraction",
            description="Extract AMSC codes from NSN details pages"
        )
        
        # Set required inputs
        self.set_required_inputs(['nsn'])
        
        # Set optional inputs
        self.set_optional_inputs(['contract_id', 'timeout', 'retry_attempts'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the AMSC extraction operation for a single NSN.
        
        Args:
            inputs: Operation inputs containing 'nsn' and optionally 'contract_id'
            context: Shared context containing the Chrome driver
            
        Returns:
            OperationResult with extracted AMSC code and closed status
        """
        try:
            nsn = inputs['nsn']
            contract_id = inputs.get('contract_id')
            timeout = inputs.get('timeout', 30)
            retry_attempts = inputs.get('retry_attempts', 3)
            
            logger.info(f"Extracting AMSC code for NSN: {nsn}")
            
            # Get the shared Chrome driver
            driver = context.get('chrome_driver')
            if not driver:
                error_msg = "Chrome driver not found in context. Run chrome_setup operation first."
                logger.error(error_msg)
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=error_msg
                )
            
            # Extract AMSC code
            amsc_code = self._extract_amsc_code(driver, nsn, timeout, retry_attempts)
            if amsc_code is None:
                error_msg = f"Failed to extract AMSC code for NSN: {nsn}"
                logger.error(error_msg)
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=error_msg
                )
            
            # Check closed status
            is_closed = self._check_closed_status(driver, nsn, timeout)
            
            logger.info(f"Successfully extracted AMSC code: {amsc_code}, Closed: {is_closed}")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'nsn': nsn,
                    'amsc_code': amsc_code,
                    'is_closed': is_closed,
                    'contract_id': contract_id
                },
                metadata={
                    'extraction_method': 'selenium',
                    'timeout_used': timeout,
                    'retry_attempts_used': retry_attempts
                }
            )
            
        except Exception as e:
            error_msg = f"AMSC extraction failed for NSN {inputs.get('nsn', 'Unknown')}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def _extract_amsc_code(self, driver, nsn: str, timeout: int, retry_attempts: int) -> Optional[str]:
        """
        Extract AMSC code from NSN details page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number to look up
            timeout: Timeout for page operations
            retry_attempts: Number of retry attempts
            
        Returns:
            AMSC code if found, None otherwise
        """
        base_url = "https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx"
        
        for attempt in range(retry_attempts):
            try:
                logger.info(f"Attempt {attempt + 1} to extract AMSC code for NSN: {nsn}")
                
                # Navigate to NSN details page
                url = f"{base_url}?value={nsn}&category=nsn"
                driver.get(url)
                
                # Handle consent page if it appears
                if self._handle_consent_page(driver, timeout):
                    logger.info("Consent page handled successfully")
                
                # Wait for page to load
                wait = WebDriverWait(driver, timeout)
                
                # Look for AMSC code in various possible locations
                amsc_code = self._find_amsc_code_in_page(driver, wait)
                
                if amsc_code:
                    logger.info(f"Found AMSC code: {amsc_code}")
                    return amsc_code
                
                # If no AMSC code found, check if page loaded correctly
                if "NSN not found" in driver.page_source or "No results" in driver.page_source:
                    logger.warning(f"NSN {nsn} not found in DIBBS")
                    return None
                
                logger.warning(f"Attempt {attempt + 1} failed - no AMSC code found")
                
                if attempt < retry_attempts - 1:
                    time.sleep(2)  # Wait before retry
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt < retry_attempts - 1:
                    time.sleep(2)  # Wait before retry
        
        logger.error(f"All {retry_attempts} attempts to extract AMSC code failed for NSN: {nsn}")
        return None
    
    def _find_amsc_code_in_page(self, driver, wait) -> Optional[str]:
        """
        Search for AMSC code in the loaded page.
        
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            
        Returns:
            AMSC code if found, None otherwise
        """
        # Common selectors where AMSC codes might appear
        amsc_selectors = [
            "//td[contains(text(), 'AMSC')]/following-sibling::td",
            "//td[contains(text(), 'AMSC')]/../td[2]",
            "//span[contains(text(), 'AMSC')]/following-sibling::span",
            "//div[contains(text(), 'AMSC')]/following-sibling::div",
            "//*[contains(text(), 'AMSC')]/following-sibling::*",
            "//*[contains(text(), 'AMSC')]/parent::*/td[2]"
        ]
        
        for selector in amsc_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                text = element.text.strip()
                if text and len(text) <= 3:  # AMSC codes are typically 1-3 characters
                    logger.info(f"Found potential AMSC code using selector: {selector}")
                    return text
            except NoSuchElementException:
                continue
        
        # Also check page source for AMSC patterns
        page_source = driver.page_source
        import re
        
        # Look for AMSC patterns in text
        amsc_patterns = [
            r'AMSC[:\s]+([A-Z0-9]{1,3})',
            r'([A-Z0-9]{1,3})\s*\(AMSC\)',
            r'AMSC\s*Code[:\s]+([A-Z0-9]{1,3})'
        ]
        
        for pattern in amsc_patterns:
            match = re.search(pattern, page_source, re.IGNORECASE)
            if match:
                amsc_code = match.group(1)
                logger.info(f"Found AMSC code using pattern: {pattern}")
                return amsc_code
        
        return None
    
    def _handle_consent_page(self, driver, timeout: int) -> bool:
        """
        Handle DLA consent page if it appears.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Timeout for consent page operations
            
        Returns:
            True if consent handled successfully, False otherwise
        """
        try:
            wait = WebDriverWait(driver, timeout)
            
            # Look for consent button (common selectors for consent pages)
            consent_selectors = [
                "//button[contains(text(), 'Ok')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Accept')]",
                "//input[@type='submit' and contains(@value, 'Ok')]",
                "//input[@type='submit' and contains(@value, 'OK')]",
                "//input[@type='submit' and contains(@value, 'Accept')]"
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    consent_button.click()
                    logger.info("Consent page handled successfully")
                    return True
                except TimeoutException:
                    continue
            
            # If no consent button found, assume no consent page
            return True
            
        except Exception as e:
            logger.warning(f"Error handling consent page: {str(e)}")
            return False
    
    def _check_closed_status(self, driver, nsn: str, timeout: int) -> bool:
        """
        Check if NSN has closed solicitations.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number
            timeout: Timeout for page operations
            
        Returns:
            True if closed, False if open, None if unknown
        """
        try:
            page_source = driver.page_source
            closed_message = f"No record of National Stock Number: {nsn} with open DIBBS Request For Quotes (RFQ) solicitations."
            
            if closed_message in page_source:
                logger.info(f"NSN {nsn} has closed solicitations")
                return True
            else:
                logger.info(f"NSN {nsn} has open solicitations")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking closed status for NSN {nsn}: {str(e)}")
            return None
    
    def can_apply_to_batch(self) -> bool:
        """
        AMSC extraction can be applied to batches of NSNs.
        
        Returns:
            True - this operation supports batch processing
        """
        return True
    
    def apply_to_batch(self, items: List[Any], inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[OperationResult]:
        """
        Apply AMSC extraction to a batch of NSNs.
        
        Args:
            items: List of NSNs to process
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each NSN
        """
        if context is None:
            context = {}
        
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} NSNs for AMSC extraction")
        
        for i, nsn in enumerate(items, 1):
            logger.info(f"Processing NSN {i}/{total_items}: {nsn}")
            
            # Create item-specific inputs
            item_inputs = inputs.copy()
            item_inputs['nsn'] = nsn
            
            # Execute operation for this NSN
            result = self.execute(item_inputs, context)
            results.append(result)
            
            # Add small delay between requests to be respectful
            if i < total_items:
                time.sleep(1)
        
        logger.info(f"Batch processing completed. {len([r for r in results if r.success])}/{total_items} successful")
        return results
