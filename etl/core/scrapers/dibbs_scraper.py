"""
DIBBS Scraper
Web scraping utilities for dibbs.bsm.dla.mil
"""

from typing import Dict, List, Optional, Any
from datetime import date
import logging
import os
import time
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class DibbsScraper:
    """Scraper for DIBBS website operations."""
    
    def __init__(self, download_dir: Optional[str] = None, headless: bool = True):
        """
        Initialize the DIBBS scraper.
        
        Args:
            download_dir: Directory to save downloaded files
            headless: Whether to run browser in headless mode
        """
        self.base_url = "https://dibbs2.bsm.dla.mil"
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        
        # Ensure download directory exists
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize webdriver
        self.driver = None
        self.headless = headless
        self._setup_driver()
        
    def _setup_driver(self):
        """Set up the Chrome webdriver with appropriate options."""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Set download directory
            prefs = {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Additional options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome webdriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize webdriver: {str(e)}")
            raise
    
    def _handle_consent_page(self, url: str) -> bool:
        """
        Handle the DLA consent page by clicking the "Ok" button.
        
        Args:
            url: URL to navigate to
            
        Returns:
            True if consent handled successfully, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for consent page to load
            wait = WebDriverWait(self.driver, 10)
            
            # Look for consent button (common selectors for consent pages)
            consent_selectors = [
                "//button[contains(text(), 'Ok')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'I Agree')]",
                "//input[@value='Ok']",
                "//input[@value='OK']",
                "//input[@value='Accept']",
                "//input[@value='I Agree']"
            ]
            
            consent_button = None
            for selector in consent_selectors:
                try:
                    consent_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if consent_button:
                logger.info("Consent button found, clicking...")
                consent_button.click()
                
                # Wait a moment for the page to process
                time.sleep(2)
                return True
            else:
                logger.info("No consent page detected, proceeding...")
                return True
                
        except Exception as e:
            logger.error(f"Error handling consent page: {str(e)}")
            return False
    
    def search_solicitation(self, solicitation_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for a solicitation by number.
        
        Args:
            solicitation_number: The solicitation number to search for
            
        Returns:
            Dict containing solicitation information or None if not found
        """
        logger.info(f"Searching for solicitation: {solicitation_number}")
        
        try:
            # Construct the RFQ URL
            last_char = solicitation_number[-1]
            rfq_url = f"{self.base_url}/Downloads/RFQ/{last_char}/{solicitation_number}.PDF"
            
            # Handle consent page and download
            if self._handle_consent_page(rfq_url):
                # Check if PDF was downloaded
                expected_filename = f"{solicitation_number}.PDF"
                expected_path = os.path.join(self.download_dir, expected_filename)
                
                # Wait for download to complete
                max_wait = 30  # seconds
                wait_time = 0
                while wait_time < max_wait:
                    if os.path.exists(expected_path):
                        logger.info(f"PDF downloaded successfully: {expected_path}")
                        
                        # Return solicitation info
                        return {
                            'number': solicitation_number,
                            'url': rfq_url,
                            'pdf_path': expected_path,
                            'filename': expected_filename
                        }
                    
                    time.sleep(1)
                    wait_time += 1
                
                logger.error(f"PDF download timeout for {solicitation_number}")
                return None
            else:
                logger.error(f"Failed to handle consent page for {solicitation_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for solicitation {solicitation_number}: {str(e)}")
            return None
    
    def download_rfq_pdf(self, solicitation_info: Dict[str, Any], 
                         output_dir: Optional[str] = None) -> Optional[str]:
        """
        Download RFQ PDF for a solicitation.
        
        Args:
            solicitation_info: Solicitation information dictionary
            output_dir: Optional output directory (overrides default)
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            solicitation_number = solicitation_info.get('number')
            if not solicitation_number:
                logger.error("No solicitation number provided")
                return None
            
            # Use provided output_dir or default
            target_dir = output_dir or self.download_dir
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            
            # Check if we already have the PDF path
            if solicitation_info.get('pdf_path') and os.path.exists(solicitation_info['pdf_path']):
                logger.info(f"PDF already exists: {solicitation_info['pdf_path']}")
                return solicitation_info['pdf_path']
            
            # If not already downloaded, search for it
            result = self.search_solicitation(solicitation_number)
            if result and result.get('pdf_path'):
                return result['pdf_path']
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading RFQ PDF: {str(e)}")
            return None
    
    def get_daily_solicitations(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Get list of solicitations for a given date.
        
        Args:
            target_date: The date to get solicitations for
            
        Returns:
            List of solicitation dictionaries
        """
        logger.info(f"Getting solicitations for date: {target_date}")
        # TODO: Implement daily solicitation fetching
        # This will require navigating to the daily listing page
        return []
    
    def get_solicitation_details(self, solicitation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a solicitation.
        
        Args:
            solicitation: Basic solicitation information
            
        Returns:
            Detailed solicitation information or None if failed
        """
        logger.info("Getting solicitation details")
        # TODO: Implement actual detail fetching logic
        return None
    
    def extract_nsn_amsc(self, nsn: str) -> Optional[str]:
        """
        Extract AMSC code from NSN Details page.
        
        Args:
            nsn: The National Stock Number to look up
            
        Returns:
            AMSC code (A, B, C, D, E, F, G, ..., S, Z) or None if failed
        """
        try:
            logger.info(f"Extracting AMSC code for NSN: {nsn}")
            
            # Construct the NSN Details URL
            nsn_url = f"https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx?value={nsn}&category=nsn"
            
            # Handle consent page and navigate to NSN details
            if not self._handle_consent_page(nsn_url):
                logger.error(f"Failed to handle consent page for NSN: {nsn}")
                return None
            
            # Wait for page to load and look for AMSC field
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            wait = WebDriverWait(self.driver, 10)
            
            # Look for text containing "AMSC:" followed by a letter
            # The AMSC field is usually displayed as "AMSC: G" or similar
            amsc_pattern = r"AMSC:\s*([A-Z])"
            
            # Get page source and search for AMSC pattern
            page_source = self.driver.page_source
            import re
            
            match = re.search(amsc_pattern, page_source)
            if match:
                amsc_code = match.group(1)
                logger.info(f"Found AMSC code: {amsc_code}")
                return amsc_code
            
            # Alternative: Look for specific elements that might contain AMSC
            try:
                # Look for any element containing "AMSC:"
                amsc_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'AMSC:')]")
                for element in amsc_elements:
                    text = element.text
                    match = re.search(amsc_pattern, text)
                    if match:
                        amsc_code = match.group(1)
                        logger.info(f"Found AMSC code in element: {amsc_code}")
                        return amsc_code
            except Exception as e:
                logger.warning(f"Alternative AMSC search failed: {str(e)}")
            
            logger.warning(f"AMSC code not found for NSN: {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting AMSC code for NSN {nsn}: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Webdriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing webdriver: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
