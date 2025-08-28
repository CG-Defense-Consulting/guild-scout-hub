#!/usr/bin/env python3
"""
Archive Downloads Navigation Operation

This operation focuses purely on navigating to archive downloads pages and returning HTML content.
It assumes the Chrome driver is already set up and only handles navigation to the archive downloads URL.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class ArchiveDownloadsNavigationOperation(BaseOperation):
    """
    Operation to navigate to archive downloads pages and return HTML content.
    
    This operation:
    - Takes date and base URL as input
    - Navigates to the archive downloads page using the provided Chrome driver
    - Constructs URL in format: "https://dibbs2.bsm.dla.mil/Downloads/RFQ/Archive/in{yy}{mm}{dd}.txt"
    - Returns the HTML content of the page
    - Does NOT handle driver setup or consent pages
    """
    
    def __init__(self):
        super().__init__(
            name="archive_downloads_navigation", 
            description="Navigate to archive downloads pages and return HTML content"
        )
        self.set_required_inputs(['date', 'chrome_driver'])
        self.set_optional_inputs(['base_url', 'timeout', 'wait_for_element'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the archive downloads navigation operation.
        
        Args:
            inputs: Operation inputs containing 'date', 'chrome_driver' and optional parameters
            context: Shared context (not used for this operation)
            
        Returns:
            OperationResult with HTML content or error information
        """
        try:
            date_input = inputs.get('date')
            driver = inputs.get('chrome_driver')
            base_url = inputs.get('base_url', 'https://dibbs2.bsm.dla.mil')
            timeout = inputs.get('timeout', 30)
            wait_for_element = inputs.get('wait_for_element', 'body')
            
            if not date_input:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required input: 'date'"
                )
            
            if not driver:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required input: 'chrome_driver'"
                )
            
            # Parse and format the date
            formatted_date = self._format_date_for_url(date_input)
            if not formatted_date:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=f"Invalid date format: {date_input}. Expected format: YYYY-MM-DD or datetime object"
                )
            
            logger.info(f"🔍 ARCHIVE NAVIGATION: Starting navigation to archive downloads page for date: {date_input}")
            logger.info(f"🔍 ARCHIVE NAVIGATION: Using base URL: {base_url}")
            logger.info(f"🔍 ARCHIVE NAVIGATION: Formatted date: {formatted_date}")
            logger.info(f"🔍 ARCHIVE NAVIGATION: Timeout: {timeout}s")
            
            # Construct archive downloads URL
            archive_url = f"{base_url}/Downloads/RFQ/Archive/in{formatted_date}.txt"
            logger.info(f"🔍 ARCHIVE NAVIGATION: Navigating to archive URL: {archive_url}")
            
            # Navigate to the archive downloads page
            driver.get(archive_url)
            logger.info(f"🔍 ARCHIVE NAVIGATION: Page loaded, current URL: {driver.current_url}")
            logger.info(f"🔍 ARCHIVE NAVIGATION: Page title: {driver.title}")
            
            # Wait for page to load
            time.sleep(1)  # Brief wait for page load
            logger.info(f"🔍 ARCHIVE NAVIGATION: Waited 1 second for page load")
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    wait = WebDriverWait(driver, timeout)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, wait_for_element)))
                    logger.info(f"🔍 ARCHIVE NAVIGATION: Element '{wait_for_element}' found")
                except TimeoutException:
                    logger.warning(f"⚠️ ARCHIVE NAVIGATION: Timeout waiting for element: {wait_for_element}")
            
            # Check if we're on the right page
            if formatted_date not in driver.current_url:
                logger.warning(f"⚠️ ARCHIVE NAVIGATION: URL doesn't contain formatted date {formatted_date}, current URL: {driver.current_url}")
            
            # Get page source
            page_source = driver.page_source
            logger.info(f"🔍 ARCHIVE NAVIGATION: Page source length: {len(page_source)} characters")
            
            logger.info(f"✅ ARCHIVE NAVIGATION: Successfully navigated to archive downloads page for date {date_input}")
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'html_content': page_source,
                    'date': date_input,
                    'formatted_date': formatted_date,
                    'url': driver.current_url,
                    'title': driver.title
                },
                metadata={
                    'navigation_successful': True, 
                    'final_url': driver.current_url,
                    'archive_date': formatted_date
                }
            )
                
        except Exception as e:
            logger.error(f"❌ ARCHIVE NAVIGATION: Error navigating to archive downloads page for date {date_input}: {str(e)}")
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=f"Archive downloads navigation operation failed: {str(e)}"
            )

    def _format_date_for_url(self, date_input) -> Optional[str]:
        """
        Format the date input for the archive downloads URL.
        
        Args:
            date_input: Date input (can be string in YYYY-MM-DD format or datetime object)
            
        Returns:
            Formatted date string in 'yymmdd' format, or None if invalid
        """
        try:
            if isinstance(date_input, str):
                # Parse string date (expected format: YYYY-MM-DD)
                date_obj = datetime.strptime(date_input, '%Y-%m-%d')
            elif isinstance(date_input, datetime):
                # Use datetime object directly
                date_obj = date_input
            else:
                logger.error(f"Unsupported date input type: {type(date_input)}")
                return None
            
            # Format as 'yymmdd' for the URL
            formatted = date_obj.strftime('%y%m%d')
            logger.debug(f"Formatted date '{date_input}' to '{formatted}'")
            return formatted
            
        except ValueError as e:
            logger.error(f"Failed to parse date '{date_input}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error formatting date '{date_input}': {str(e)}")
            return None

    def can_apply_to_batch(self) -> bool:
        """This operation can be applied to batches of dates."""
        return True

    def apply_to_batch(self, items: list, inputs: Dict[str, Any], 
                      context: Dict[str, Any]) -> list:
        """
        Apply archive downloads navigation to a batch of dates.
        
        Args:
            items: List of dates to navigate to
            inputs: Operation inputs
            context: Shared workflow context
            
        Returns:
            List of OperationResult objects for each date
        """
        results = []
        total_items = len(items)
        
        logger.info(f"🔍 ARCHIVE NAVIGATION: Processing batch of {total_items} dates")
        
        for i, date_item in enumerate(items):
            logger.info(f"🔍 ARCHIVE NAVIGATION: Processing date {i+1}/{total_items}: {date_item}")
            
            # Create inputs for this specific date
            date_inputs = inputs.copy()
            date_inputs['date'] = date_item
            
            # Execute navigation for this date
            result = self._execute(date_inputs, context)
            results.append(result)
            
            # Brief pause between navigations to avoid overwhelming the server
            if i < total_items - 1:
                time.sleep(1)
        
        # Log batch completion
        successful = len([r for r in results if r.success])
        logger.info(f"🔍 ARCHIVE NAVIGATION: Batch processing completed. {successful}/{total_items} successful")
        return results
