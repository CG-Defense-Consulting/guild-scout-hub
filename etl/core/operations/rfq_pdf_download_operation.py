#!/usr/bin/env python3
"""
RFQ PDF Download Operation

This operation downloads RFQ PDFs from DIBBS using solicitation numbers.
"""

import logging
import time
import os
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class RfqPdfDownloadOperation(BaseOperation):
    """
    Operation to download RFQ PDFs from DIBBS.
    
    This operation:
    - Navigates to DIBBS RFQ pages using solicitation numbers
    - Downloads RFQ PDFs
    - Handles consent pages if needed
    """
    
    def __init__(self):
        super().__init__(
            name="rfq_pdf_download",
            description="Download RFQ PDFs from DIBBS"
        )
        self.set_required_inputs(['solicitation_number'])
        self.set_optional_inputs(['timeout', 'retry_attempts', 'download_dir', 'base_url'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute RFQ PDF download operation.
        
        Args:
            inputs: Operation inputs including solicitation_number and optional parameters
            context: Shared workflow context containing the Chrome driver
            
        Returns:
            OperationResult with download success status and metadata
        """
        try:
            # Get driver from context (set by ChromeSetupOperation)
            driver = context.get('chrome_driver')
            if not driver:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error="Chrome driver not found in context. Make sure ChromeSetupOperation runs first.",
                    metadata={'context_keys': list(context.keys())}
                )
            
            solicitation_number = inputs['solicitation_number']
            timeout = inputs.get('timeout', 30)
            retry_attempts = inputs.get('retry_attempts', 3)
            download_dir = inputs.get('download_dir', context.get('chrome_download_dir', os.path.join(os.getcwd(), "downloads")))
            base_url = inputs.get('base_url', 'https://www.dibbs.bsm.dla.mil/RFQ/RFQ.aspx')
            
            logger.info(f"Starting RFQ PDF download for solicitation: {solicitation_number}")
            
            # Navigate to RFQ page
            rfq_url = f"{base_url}?value={solicitation_number}"
            logger.info(f"Navigating to: {rfq_url}")
            
            driver.get(rfq_url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, timeout)
            
            # Check for consent page and handle it
            if self._is_consent_page(driver):
                logger.info(f"Consent page detected for {solicitation_number}, handling...")
                if not self._handle_consent_page(driver, wait):
                    return OperationResult(
                        success=False,
                        status=OperationStatus.FAILED,
                        error=f"Failed to handle consent page for {solicitation_number}",
                        metadata={'solicitation_number': solicitation_number}
                    )
            
            # Look for PDF download link
            pdf_downloaded = self._download_rfq_pdf(driver, wait, solicitation_number, download_dir)
            
            if pdf_downloaded:
                logger.info(f"Successfully downloaded RFQ PDF for {solicitation_number}")
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={'pdf_downloaded': True, 'solicitation_number': solicitation_number},
                    metadata={'solicitation_number': solicitation_number, 'download_dir': download_dir}
                )
            else:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=f"Failed to download RFQ PDF for {solicitation_number}",
                    metadata={'solicitation_number': solicitation_number}
                )
            
        except Exception as e:
            error_msg = f"RFQ PDF download operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg,
                metadata={'solicitation_number': inputs.get('solicitation_number', 'unknown'), 'error_type': type(e).__name__}
            )
    
    def _is_consent_page(self, driver) -> bool:
        """Check if we're on a consent page."""
        try:
            # Look for consent page indicators
            consent_indicators = [
                "//h1[contains(text(), 'Consent')]",
                "//h1[contains(text(), 'Disclaimer')]",
                "//input[@value='I Agree']",
                "//input[@value='Accept']"
            ]
            
            for indicator in consent_indicators:
                if driver.find_elements(By.XPATH, indicator):
                    return True
            
            return False
        except Exception:
            return False
    
    def _handle_consent_page(self, driver, wait) -> bool:
        """Handle DLA consent page."""
        try:
            # Look for consent button
            consent_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='I Agree' or @value='Accept' or @value='Continue']"))
            )
            
            logger.info("Clicking consent button...")
            consent_button.click()
            
            # Wait for page to load after consent
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle consent page: {str(e)}")
            return False
    
    def _download_rfq_pdf(self, driver, wait, solicitation_number: str, download_dir: str) -> bool:
        """Download the RFQ PDF."""
        try:
            # Look for PDF download link
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf') or contains(text(), 'PDF') or contains(text(), 'Download')]")
            
            if not pdf_links:
                logger.warning(f"No PDF download links found for {solicitation_number}")
                return False
            
            # Click the first PDF link
            pdf_link = pdf_links[0]
            logger.info(f"Found PDF link: {pdf_link.text}")
            
            # Get the href if it exists
            href = pdf_link.get_attribute('href')
            if href:
                logger.info(f"PDF URL: {href}")
                # Navigate directly to PDF URL
                driver.get(href)
                time.sleep(3)  # Wait for download to start
            else:
                # Click the link
                pdf_link.click()
                time.sleep(3)  # Wait for download to start
            
            # Check if file was downloaded
            expected_filename = f"{solicitation_number}.pdf"
            file_path = os.path.join(download_dir, expected_filename)
            
            # Wait for file to appear
            max_wait = 30
            for _ in range(max_wait):
                if os.path.exists(file_path):
                    logger.info(f"PDF downloaded successfully: {file_path}")
                    return True
                time.sleep(1)
            
            logger.warning(f"PDF download timeout for {solicitation_number}")
            return False
            
        except Exception as e:
            logger.error(f"Error downloading PDF for {solicitation_number}: {str(e)}")
            return False
