#!/usr/bin/env python3
"""
DIBBS Text File Download Operation

This operation handles downloading text files from the DIBBS website.
It works with the archive downloads page where the current URL is a direct download link.
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class DibbsTextFileDownloadOperation(BaseOperation):
    """
    Operation to download text files from the DIBBS website.
    
    This operation:
    1. Assumes the Chrome driver is already on the archive downloads page
    2. Triggers the download of the text file
    3. Waits for the download to complete
    4. Returns the file path for further processing
    """
    
    def __init__(self):
        super().__init__(
            name="dibbs_text_file_download",
            description="Download text file from DIBBS archive downloads page"
        )
        self.set_required_inputs([])
        self.set_optional_inputs(['timeout', 'retry_attempts', 'download_dir'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the DIBBS text file download operation.
        
        Args:
            inputs: Operation inputs (not used for this operation)
            context: Shared context containing the Chrome driver
            
        Returns:
            OperationResult with download file path or error
        """
        try:
            logger.info("🔍 TEXT FILE DOWNLOAD: Starting DIBBS text file download operation")
            
            # Get Chrome driver from context
            driver = context.get('chrome_driver')
            if not driver:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Missing required context: 'chrome_driver'"
                )
            
            # Get optional parameters
            timeout = inputs.get('timeout', 30)
            retry_attempts = inputs.get('retry_attempts', 3)
            download_dir = inputs.get('download_dir', os.getenv('DIBBS_DOWNLOAD_DIR', './downloads'))
            
            # Ensure download directory exists
            os.makedirs(download_dir, exist_ok=True)
            
            # Get current URL to understand what we're downloading
            current_url = driver.current_url
            logger.info(f"🔍 TEXT FILE DOWNLOAD: Current URL: {current_url}")
            
            # Note: Chrome download preferences are not needed for direct text content extraction
            # We'll get the content directly from the page source
            
            # The current page should be a direct download link
            # For text files, we can either:
            # 1. Trigger download by clicking/refreshing
            # 2. Get the content directly if it's a text response
            
            # Try to get the content directly first
            try:
                logger.info("🔍 TEXT FILE DOWNLOAD: Attempting to get text content directly...")
                
                # Wait for page to load completely
                wait = WebDriverWait(driver, timeout)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                
                # Get the page source/content
                page_content = driver.page_source
                
                # Check if this is actually text content or an HTML page
                if page_content.startswith('<!DOCTYPE html') or '<html' in page_content:
                    logger.info("🔍 TEXT FILE DOWNLOAD: Page contains HTML, treating as download page")
                    
                    # This is an HTML page, so we need to trigger the download
                    # Try refreshing the page to trigger download
                    logger.info("🔍 TEXT FILE DOWNLOAD: Refreshing page to trigger download...")
                    driver.refresh()
                    time.sleep(2)  # Wait for refresh
                    
                    # Check if we now have text content
                    page_content = driver.page_source
                    if not (page_content.startswith('<!DOCTYPE html') or '<html' in page_content):
                        logger.info("🔍 TEXT FILE DOWNLOAD: Successfully got text content after refresh")
                    else:
                        logger.info("🔍 TEXT FILE DOWNLOAD: Still HTML content, will try alternative approach")
                        
                        # Alternative: try to get the text content from the page
                        # try:
                        #     # Look for text content in the page
                        #     text_elements = driver.find_elements(By.TAG_NAME, 'pre')
                        #     if text_elements:
                        #         page_content = text_elements[0].text
                        #         logger.info("🔍 TEXT FILE DOWNLOAD: Found text content in <pre> element")
                        #     else:
                        #         # Try to get text from body
                        #         body_element = driver.find_element(By.TAG_NAME, 'body')
                        #         page_content = body_element.text
                        #         logger.info("🔍 TEXT FILE DOWNLOAD: Extracted text content from body")
                        # except Exception as e:
                        #     logger.warning(f"⚠️ TEXT FILE DOWNLOAD: Could not extract text content: {e}")
                        #     page_content = ""
                else:
                    logger.info("🔍 TEXT FILE DOWNLOAD: Page contains direct text content")
                
                # # If we have text content, save it to file
                # if page_content and not page_content.startswith('<!DOCTYPE html'):
                #     # erase download_dir completely
                #     #for file in os.listdir(download_dir):
                #     #    os.remove(os.path.join(download_dir, file))
                    
                #     # create a new file with the current date and time
                #     file_name = datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt'
                #     file_path = os.path.join(download_dir, file_name)

                #     # Write the content to file
                #     with open(file_path, 'w', encoding='utf-8') as f:
                #         f.write(page_content)
                    
                #     logger.info(f"🔍 TEXT FILE DOWNLOAD: Successfully saved text content to: {file_path}")
                #     logger.info(f"🔍 TEXT FILE DOWNLOAD: File size: {len(page_content)} characters")
                
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={
                        'file_path': os.path.join(download_dir, sorted(os.listdir(download_dir))[-1]),
                        'content_length': len(page_content)
                    },
                    metadata={
                        'download_method': 'direct_content',
                        'source_url': current_url
                    }
                )
                    
            except Exception as e:
                logger.error(f"❌ TEXT FILE DOWNLOAD: Error getting text content: {str(e)}")
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=f"Failed to get text content: {str(e)}"
                )
                
        except Exception as e:
            error_msg = f"Text file download operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def can_apply_to_batch(self) -> bool:
        """
        Text file download cannot be applied to batches.
        
        Returns:
            False - this operation is not batchable
        """
        return False
