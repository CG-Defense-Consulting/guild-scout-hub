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
            
            # Handle consent page first
            if self._handle_consent_page(rfq_url):
                # Now download the PDF using requests with session cookies
                pdf_path = self._download_pdf_with_requests(rfq_url, solicitation_number)
                
                if pdf_path and os.path.exists(pdf_path):
                    logger.info(f"PDF downloaded successfully: {pdf_path}")
                    
                    # Verify the PDF is valid
                    if self._verify_pdf(pdf_path):
                        # Return solicitation info
                        return {
                            'number': solicitation_number,
                            'url': rfq_url,
                            'pdf_path': pdf_path,
                            'filename': f"{solicitation_number}.PDF"
                        }
                    else:
                        logger.error(f"Downloaded PDF is corrupted: {pdf_path}")
                        return None
                else:
                    logger.error(f"Failed to download PDF for {solicitation_number}")
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
    
    def _download_pdf_with_requests(self, pdf_url: str, solicitation_number: str) -> Optional[str]:
        """
        Download PDF using requests with session cookies from Selenium.
        
        Args:
            pdf_url: URL of the PDF to download
            solicitation_number: Solicitation number for filename
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            # Get cookies from Selenium session
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
            
            # Use requests to download the PDF
            logger.info(f"Downloading PDF with requests: {pdf_url}")
            
            # Set headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/octet-stream,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(pdf_url, cookies=cookies, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'octet-stream' not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Check PDF magic bytes
            if not response.content.startswith(b'%PDF'):
                logger.error("Downloaded content is not a valid PDF (missing PDF header)")
                return None
            
            # Save the PDF
            filename = f"{solicitation_number}.PDF"
            pdf_path = os.path.join(self.download_dir, filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"PDF downloaded successfully: {pdf_path} ({len(response.content)} bytes)")
            return pdf_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading PDF: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF with requests: {str(e)}")
            return None
    
    def _verify_pdf(self, pdf_path: str) -> bool:
        """
        Verify that the downloaded file is a valid PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if PDF is valid, False otherwise
        """
        try:
            # Check file exists and has content
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file does not exist: {pdf_path}")
                return False
            
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                logger.error(f"PDF file is empty: {pdf_path}")
                return False
            
            # Check PDF magic bytes
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'%PDF'):
                    logger.error(f"File is not a valid PDF (missing PDF header): {pdf_path}")
                    return False
            
            # Try to read PDF end marker
            with open(pdf_path, 'rb') as f:
                f.seek(-1024, 2)  # Read last 1024 bytes
                tail = f.read()
                if b'%%EOF' not in tail:
                    logger.warning(f"PDF may be truncated (missing EOF marker): {pdf_path}")
                    # Don't fail here as some PDFs might still be valid
            
            logger.info(f"PDF verification passed: {pdf_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying PDF: {str(e)}")
            return False

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
            nsn_url = f"https://dibbs2.bsm.dla.mil/RFQ/RFQNsn.aspx?value={nsn}&category=nsn"
            logger.info(f"Navigating to NSN URL: {nsn_url}")
            
            # Handle consent page and navigate to NSN details
            logger.info(f"About to handle consent page for URL: {nsn_url}")
            if not self._handle_consent_page(nsn_url):
                logger.error(f"Failed to handle consent page for NSN: {nsn}")
                return None
            
            logger.info("Consent page handled successfully, waiting for NSN page to load...")
            logger.info(f"After consent page, current URL: {self.driver.current_url}")
            
            # Wait a moment for the page to fully load
            import time
            time.sleep(2)
            logger.info(f"After wait, current URL: {self.driver.current_url}")
            
            # Wait for page to load and look for AMSC field
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            wait = WebDriverWait(self.driver, 10)
            
            # Wait for page to be fully loaded
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("Page loaded successfully")
            except Exception as e:
                logger.warning(f"Page load wait failed: {str(e)}")
            
            # Get current URL to confirm we're on the right page
            current_url = self.driver.current_url
            logger.info(f"Current page URL: {current_url}")
            
            # Check if we're on the expected NSN page
            if "RFQNsn.aspx" in current_url:
                logger.info("✅ Successfully navigated to NSN details page")
            else:
                logger.warning(f"⚠️ Unexpected page URL: {current_url}")
                logger.warning("Expected URL to contain 'RFQNsn.aspx'")
            
            # Get page title for debugging
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            # Get page source first, then log info about it
            page_source = self.driver.page_source
            import re
            
            # Log additional page info
            logger.info(f"Page source length: {len(page_source)} characters")
            logger.info(f"Page source contains 'AMSC:': {'AMSC:' in page_source}")
            logger.info(f"Page source contains 'AMSC': {'AMSC' in page_source}")
            logger.info(f"Page source contains 'amsc': {'amsc' in page_source.lower()}")
            
            # Log a small sample of the page source to see what we're getting
            if len(page_source) > 0:
                sample_start = page_source[:200]
                sample_end = page_source[-200:] if len(page_source) > 200 else ""
                logger.info(f"Page source sample (start): {sample_start}")
                logger.info(f"Page source sample (end): {sample_end}")
                
                # Check for common HTML elements that should be present
                logger.info(f"Page contains <html>: {'<html' in page_source.lower()}")
                logger.info(f"Page contains <body>: {'<body' in page_source.lower()}")
                logger.info(f"Page contains <title>: {'<title' in page_source.lower()}")
            else:
                logger.warning("Page source is empty!")
            
            # Look for text containing "AMSC:" followed by a letter
            # The AMSC field is usually displayed as "AMSC: G" or similar
            amsc_pattern = r"AMSC:\s*([A-Z])"
            
            # Log detailed page source preview
            logger.info(f"Page source preview (first 500 chars): {page_source[:500]}")
            logger.info(f"Page source preview (last 500 chars): {page_source[-500:]}")
            
            # Log a sample of the page source around where AMSC might be
            amsc_index = page_source.find("AMSC:")
            if amsc_index != -1:
                start = max(0, amsc_index - 100)
                end = min(len(page_source), amsc_index + 200)
                sample_text = page_source[start:end]
                logger.info(f"Found 'AMSC:' at position {amsc_index}, sample context:")
                logger.info(f"Context: ...{sample_text}...")
            else:
                logger.warning("'AMSC:' text not found in page source")
            
            # Search for AMSC pattern in page source
            match = re.search(amsc_pattern, page_source)
            if match:
                amsc_code = match.group(1)
                logger.info(f"✓ Found AMSC code via regex: {amsc_code}")
                return amsc_code
            
            logger.info("Regex search failed, trying alternative search methods...")
            
            # Alternative 1: Look for any element containing "AMSC:"
            try:
                logger.info("Searching for elements containing 'AMSC:' text...")
                amsc_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'AMSC:')]")
                logger.info(f"Found {len(amsc_elements)} elements containing 'AMSC:' text")
                
                for i, element in enumerate(amsc_elements):
                    text = element.text
                    logger.info(f"Element {i+1} text: '{text}'")
                    match = re.search(amsc_pattern, text)
                    if match:
                        amsc_code = match.group(1)
                        logger.info(f"✓ Found AMSC code in element {i+1}: {amsc_code}")
                        return amsc_code
            except Exception as e:
                logger.warning(f"Alternative AMSC search failed: {str(e)}")
            
            # Alternative 2: Look for specific HTML structure (like the <strong> tags in your example)
            try:
                logger.info("Searching for <strong> tags that might contain AMSC...")
                strong_elements = self.driver.find_elements(By.TAG_NAME, "strong")
                logger.info(f"Found {len(strong_elements)} <strong> elements")
                
                for i, element in enumerate(strong_elements):
                    text = element.text.strip()
                    if text and len(text) == 1 and text.isalpha():
                        logger.info(f"Strong element {i+1} contains single letter: '{text}'")
                        # Check if this is near AMSC text
                        parent_text = element.find_element(By.XPATH, "..").text
                        if "AMSC:" in parent_text:
                            logger.info(f"✓ Found AMSC code in <strong> tag: {text}")
                            return text
            except Exception as e:
                logger.warning(f"Strong tag search failed: {str(e)}")
            
            # Alternative 3: Look for legend elements (common in forms)
            try:
                logger.info("Searching for <legend> elements...")
                legend_elements = self.driver.find_elements(By.TAG_NAME, "legend")
                logger.info(f"Found {len(legend_elements)} <legend> elements")
                
                for i, element in enumerate(legend_elements):
                    text = element.text
                    logger.info(f"Legend element {i+1}: '{text}'")
                    if "AMSC:" in text:
                        match = re.search(amsc_pattern, text)
                        if match:
                            amsc_code = match.group(1)
                            logger.info(f"✓ Found AMSC code in legend: {amsc_code}")
                            return amsc_code
            except Exception as e:
                logger.warning(f"Legend search failed: {str(e)}")
            
            # Alternative 4: Look for the specific HTML structure from the user's example
            # The AMSC code "B" is in a <strong> tag that's a sibling to "AMSC:" text
            try:
                logger.info("Searching for specific HTML structure: <legend> with <strong> containing AMSC...")
                legend_elements = self.driver.find_elements(By.TAG_NAME, "legend")
                
                for i, legend in enumerate(legend_elements):
                    logger.info(f"Examining legend element {i+1}")
                    
                    # Look for <strong> tags within this legend
                    strong_elements = legend.find_elements(By.TAG_NAME, "strong")
                    logger.info(f"  Found {len(strong_elements)} <strong> elements in legend {i+1}")
                    
                    for j, strong in enumerate(strong_elements):
                        strong_text = strong.text.strip()
                        logger.info(f"    Strong element {j+1} text: '{strong_text}'")
                        
                        # Check if this strong element contains a single letter (potential AMSC)
                        if strong_text and len(strong_text) == 1 and strong_text.isalpha():
                            logger.info(f"    Found single letter: '{strong_text}'")
                            
                            # Check if this legend contains "AMSC:" text
                            legend_text = legend.text
                            if "AMSC:" in legend_text:
                                logger.info(f"    Legend contains 'AMSC:' text")
                                
                                # Verify this is the AMSC code by checking the context
                                # Look for the text pattern around this strong element
                                try:
                                    # Get the parent text to see the full context
                                    parent = strong.find_element(By.XPATH, "..")
                                    parent_text = parent.text
                                    logger.info(f"    Parent text context: '{parent_text}'")
                                    
                                    # Check if this looks like an AMSC field
                                    if "AMSC:" in parent_text and strong_text in parent_text:
                                        logger.info(f"✓ Found AMSC code '{strong_text}' in <strong> tag within <legend>")
                                        return strong_text
                                except Exception as e:
                                    logger.warning(f"    Error checking parent context: {str(e)}")
                                    
            except Exception as e:
                logger.warning(f"Specific HTML structure search failed: {str(e)}")
            
            # Alternative 5: Look for any text that matches the expected pattern
            try:
                logger.info("Searching for any text matching AMSC pattern...")
                # Look for text nodes that contain "AMSC:" followed by a letter
                amsc_text_elements = self.driver.find_elements(By.XPATH, "//text()[contains(., 'AMSC:')]")
                logger.info(f"Found {len(amsc_text_elements)} text nodes containing 'AMSC:'")
                
                for i, text_element in enumerate(amsc_text_elements):
                    text_content = text_element.text
                    logger.info(f"Text node {i+1}: '{text_content}'")
                    
                    # Look for the pattern "AMSC: X" where X is a letter
                    match = re.search(r'AMSC:\s*([A-Z])', text_content)
                    if match:
                        amsc_code = match.group(1)
                        logger.info(f"✓ Found AMSC code in text node: {amsc_code}")
                        return amsc_code
                        
            except Exception as e:
                logger.warning(f"Text node search failed: {str(e)}")
            
            # Log the full page source for debugging if AMSC not found
            logger.error(f"AMSC code not found for NSN: {nsn}")
            logger.error("Full page source for debugging:")
            logger.error(page_source)
            return None
            
        except Exception as e:
            logger.error(f"Error extracting AMSC code for NSN {nsn}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
