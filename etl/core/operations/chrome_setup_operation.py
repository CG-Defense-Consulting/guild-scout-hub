"""
Chrome Setup Operation

This operation initializes Chrome and ChromeDriver once and makes them available
to other operations through the shared context. This eliminates the need to
reinitialize the browser for each individual operation.
"""

import logging
import os
from typing import Any, Dict, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

class ChromeSetupOperation(BaseOperation):
    """
    Operation that sets up Chrome and ChromeDriver for use by other operations.
    
    This operation:
    1. Initializes Chrome with appropriate options
    2. Sets up ChromeDriver
    3. Stores the driver instance in the shared context
    4. Can be reused by multiple subsequent operations
    """
    
    def __init__(self, headless: bool = True, download_dir: str = None):
        """
        Initialize the Chrome setup operation.
        
        Args:
            headless: Whether to run Chrome in headless mode
            download_dir: Directory for downloads (optional)
        """
        super().__init__(
            name="chrome_setup",
            description="Initialize Chrome and ChromeDriver for web scraping operations"
        )
        
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        
        # Set required inputs (none for this operation)
        self.set_required_inputs([])
        
        # Set optional inputs
        self.set_optional_inputs(['chrome_options', 'download_dir'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the Chrome setup operation.
        
        Args:
            inputs: Operation inputs (not used for this operation)
            context: Shared context where the driver will be stored
            
        Returns:
            OperationResult with success status and driver metadata
        """
        try:
            logger.info("Setting up Chrome and ChromeDriver...")
            
            # Use provided download directory or default
            download_dir = inputs.get('download_dir', self.download_dir)
            
            # Ensure download directory exists
            os.makedirs(download_dir, exist_ok=True)
            logger.info(f"Using download directory: {download_dir}")
            
            # Set up Chrome options
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
                logger.info("Chrome will run in headless mode")
            
            # Set download preferences
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Additional options for stability and performance
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Don't load images for faster scraping
            
            # Allow custom options to be passed in
            custom_options = inputs.get('chrome_options', {})
            for option, value in custom_options.items():
                if option.startswith('--'):
                    chrome_options.add_argument(f"{option}={value}")
                else:
                    chrome_options.add_argument(option)
            
            logger.info("Chrome options configured successfully")
            
            # Initialize the webdriver
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.implicitly_wait(2)  # Reduced from 10 seconds
                logger.info("Chrome webdriver initialized successfully")
                
            except WebDriverException as e:
                # Try with service if direct initialization fails
                logger.warning(f"Direct Chrome initialization failed, trying with service: {e}")
                try:
                    # Look for chromedriver in common locations
                    chromedriver_paths = [
                        "/usr/local/bin/chromedriver",
                        "/usr/bin/chromedriver",
                        "./chromedriver",
                        "chromedriver"
                    ]
                    
                    chromedriver_path = None
                    for path in chromedriver_paths:
                        if os.path.exists(path):
                            chromedriver_path = path
                            break
                    
                    if chromedriver_path:
                        service = Service(executable_path=chromedriver_path)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver.implicitly_wait(2)  # Reduced from 10 seconds
                        logger.info(f"Chrome webdriver initialized with service from {chromedriver_path}")
                    else:
                        raise WebDriverException("ChromeDriver not found in common locations")
                        
                except WebDriverException as service_error:
                    error_msg = f"Failed to initialize Chrome webdriver: {str(service_error)}"
                    logger.error(error_msg)
                    return OperationResult(
                        success=False,
                        status=OperationStatus.FAILED,
                        error=error_msg
                    )
            
            # Store driver in shared context for other operations
            context['chrome_driver'] = driver
            context['chrome_download_dir'] = download_dir
            context['chrome_headless'] = self.headless
            
            logger.info("Chrome setup completed successfully")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'driver': driver,
                    'driver_ready': True,
                    'download_dir': download_dir,
                    'headless': self.headless
                },
                metadata={
                    'chrome_version': driver.capabilities.get('browserVersion', 'Unknown'),
                    'chromedriver_version': driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'Unknown')
                }
            )
            
        except Exception as e:
            error_msg = f"Chrome setup failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def cleanup(self, context: Dict[str, Any]) -> None:
        """
        Clean up Chrome resources.
        
        Args:
            context: Shared context containing the Chrome driver
        """
        try:
            driver = context.get('chrome_driver')
            if driver:
                logger.info("Closing Chrome webdriver...")
                driver.quit()
                context.pop('chrome_driver', None)
                logger.info("Chrome webdriver closed successfully")
        except Exception as e:
            logger.warning(f"Error during Chrome cleanup: {str(e)}")
    
    def can_apply_to_batch(self) -> bool:
        """
        Chrome setup cannot be applied to batches - it's a one-time setup operation.
        
        Returns:
            False - this operation is not batchable
        """
        return False
