#!/usr/bin/env python3
"""
NSN Page Navigation Operation

This operation focuses purely on navigating to NSN pages and returning HTML content.
It assumes the Chrome driver is already set up and only handles navigation.
"""

import logging
import time
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class NsnPageNavigationOperation(BaseOperation):
    """
    Operation to navigate to NSN pages and return HTML content.
    
    This operation:
    - Takes NSN and base URL as input
    - Navigates to the NSN page using the provided Chrome driver
    - Returns the HTML content of the page
    - Does NOT handle driver setup or consent pages
    """
    
    def __init__(self):
        super().__init__(
            name="nsn_page_navigation", 
            description="Navigate to NSN pages and return HTML content"
        )
        self.set_required_inputs(['nsn', 'chrome_driver'])
        self.set_optional_inputs(['base_url', 'timeout', 'wait_for_element'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the NSN page navigation operation.
        
        Args:
            inputs: Operation inputs containing 'nsn', 'chrome_driver' and optional parameters
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with HTML content or error information
        """
        try:
            nsn = inputs.get('nsn')
            driver = inputs.get('chrome_driver')
            base_url = inputs.get('base_url', 'https://www.dibbs.bsm.dla.mil')
            timeout = inputs.get('timeout', 30)
            wait_for_element = inputs.get('wait_for_element', 'body')
            
            if not nsn:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required input: 'nsn'"
                )
            
            if not driver:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required input: 'chrome_driver'"
                )
            
            logger.info(f"🔍 NSN NAVIGATION: Starting navigation to NSN page for: {nsn}")
            logger.info(f"🔍 NSN NAVIGATION: Using base URL: {base_url}")
            logger.info(f"🔍 NSN NAVIGATION: Timeout: {timeout}s")
            
            # Construct NSN URL
            nsn_url = f"{base_url}/rfq/rfqnsn.aspx?value={nsn}"
            logger.info(f"🔍 NSN NAVIGATION: Navigating to NSN URL: {nsn_url}")
            
            # Navigate to the NSN page
            driver.get(nsn_url)
            logger.info(f"🔍 NSN NAVIGATION: Page loaded, current URL: {driver.current_url}")
            logger.info(f"🔍 NSN NAVIGATION: Page title: {driver.title}")
            
            # Wait for page to load
            time.sleep(1)  # Brief wait for page load
            logger.info(f"🔍 NSN NAVIGATION: Waited 1 second for page load")
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    wait = WebDriverWait(driver, timeout)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, wait_for_element)))
                    logger.info(f"🔍 NSN NAVIGATION: Element '{wait_for_element}' found")
                except TimeoutException:
                    logger.warning(f"⚠️ NSN NAVIGATION: Timeout waiting for element: {wait_for_element}")
            
            # Check if we're on the right page
            if nsn not in driver.current_url:
                logger.warning(f"⚠️ NSN NAVIGATION: URL doesn't contain NSN {nsn}, current URL: {driver.current_url}")
            
            # Get page source
            page_source = driver.page_source
            logger.info(f"🔍 NSN NAVIGATION: Page source length: {len(page_source)} characters")
            
            logger.info(f"✅ NSN NAVIGATION: Successfully navigated to NSN page for {nsn}")
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'html_content': page_source,
                    'nsn': nsn,
                    'url': driver.current_url,
                    'title': driver.title
                },
                metadata={'navigation_successful': True, 'final_url': driver.current_url}
            )
                
        except Exception as e:
            logger.error(f"❌ NSN NAVIGATION: Error navigating to NSN page for {nsn}: {str(e)}")
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"NSN page navigation operation failed: {str(e)}"
            )

    def can_apply_to_batch(self) -> bool:
        """This operation can be applied to batches of NSNs."""
        return True

    def apply_to_batch(self, items: list, inputs: Dict[str, Any], 
                      context: Dict[str, Any]) -> list:
        """
        Apply NSN page navigation to a batch of NSNs.
        
        Args:
            items: List of NSNs to navigate to
            inputs: Operation inputs
            context: Shared workflow context
            
        Returns:
            List of OperationResult objects for each NSN
        """
        results = []
        total_items = len(items)
        
        logger.info(f"🔍 NSN NAVIGATION: Processing batch of {total_items} NSNs")
        
        for i, nsn in enumerate(items):
            logger.info(f"🔍 NSN NAVIGATION: Processing NSN {i+1}/{total_items}: {nsn}")
            
            # Create inputs for this specific NSN
            nsn_inputs = inputs.copy()
            nsn_inputs['nsn'] = nsn
            
            # Execute navigation for this NSN
            result = self._execute(nsn_inputs, context)
            results.append(result)
            
            # Brief pause between navigations to avoid overwhelming the server
            if i < total_items - 1:
                time.sleep(1)
        
        # Log batch completion
        successful = len([r for r in results if r.success])
        logger.info(f"🔍 NSN NAVIGATION: Batch processing completed. {successful}/{total_items} successful")
        return results
