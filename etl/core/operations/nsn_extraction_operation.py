#!/usr/bin/env python3
"""
NSN Extraction Operation

This operation focuses purely on extracting NSN data from DIBBS pages.
It does NOT handle consent pages or closed status checking itself.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_operation import BaseOperation, OperationStatus, OperationResult

logger = logging.getLogger(__name__)

class NsnExtractionOperation(BaseOperation):
    """
    Operation to extract NSN data from DIBBS pages.
    
    This operation:
    - Navigates to NSN pages
    - Extracts specified fields (AMSC code, description, part number, etc.)
    - Checks for closed solicitation status if requested
    - Does NOT handle consent pages (use ConsentPageOperation for that)
    - Does NOT handle closed status checking (use ClosedSolicitationCheckOperation for that)
    """
    
    def __init__(self):
        super().__init__(
            name="nsn_extraction",
            description="Extract NSN data from DIBBS pages"
        )
        self.set_required_inputs(['driver', 'nsn'])
        self.set_optional_inputs(['timeout', 'retry_attempts', 'extract_fields', 'base_url', 'check_closed_status'])

    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute NSN extraction operation.
        
        Args:
            inputs: Operation inputs including driver, nsn, and optional parameters
            context: Shared workflow context
            
        Returns:
            OperationResult with extracted data or error information
        """
        try:
            driver = inputs['driver']
            nsn = inputs['nsn']
            timeout = inputs.get('timeout', 30)
            retry_attempts = inputs.get('retry_attempts', 3)
            extract_fields = inputs.get('extract_fields', ['amsc_code', 'description', 'part_number'])
            base_url = inputs.get('base_url', 'https://www.dibbs.bsm.dla.mil/RFQ/RFQNsn.aspx')
            check_closed_status = inputs.get('check_closed_status', False)
            
            logger.info(f"Starting NSN extraction for NSN: {nsn}")
            
            # Extract NSN data
            nsn_data = self._extract_nsn_data(
                driver, nsn, base_url, timeout, retry_attempts, extract_fields
            )
            
            if not nsn_data:
                return OperationResult(
                    success=False,
                    status=OperationStatus.FAILED,
                    error=f"Failed to extract data for NSN: {nsn}",
                    metadata={'nsn': nsn, 'attempts': retry_attempts}
                )
            
            # Check for closed solicitation status if requested
            if check_closed_status:
                logger.info(f"Checking closed solicitation status for NSN: {nsn}")
                closed_status = self._check_closed_solicitation_status(driver, nsn)
                nsn_data['closed'] = closed_status
                logger.info(f"Closed solicitation status for NSN {nsn}: {closed_status}")
            
            logger.info(f"Successfully extracted data for NSN: {nsn}")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data=nsn_data,
                metadata={'nsn': nsn, 'fields_extracted': list(nsn_data.keys())}
            )
            
        except Exception as e:
            error_msg = f"NSN extraction operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg,
                metadata={'nsn': inputs.get('nsn', 'unknown'), 'error_type': type(e).__name__}
            )

    def _extract_nsn_data(self, driver, nsn: str, base_url: str, timeout: int,
                          retry_attempts: int, extract_fields: List[str]) -> Optional[Dict[str, Any]]:
        """
        Extract NSN data with retry logic.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number to extract
            base_url: Base URL for NSN lookup
            timeout: Timeout for page operations
            retry_attempts: Number of retry attempts
            extract_fields: List of fields to extract
            
        Returns:
            Dictionary with extracted data or None if failed
        """
        for attempt in range(retry_attempts):
            try:
                logger.info(f"Attempt {attempt + 1}/{retry_attempts} for NSN: {nsn}")
                
                # Navigate to NSN page
                url = f"{base_url}?value={nsn}&category=nsn"
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if NSN was found
                if self._is_nsn_not_found(driver, nsn):
                    logger.warning(f"NSN {nsn} not found on DIBBS")
                    return None
                
                # Extract requested fields
                extracted_data = {}
                for field in extract_fields:
                    value = self._extract_field(driver, field, nsn)
                    if value is not None:
                        extracted_data[field] = value
                
                if extracted_data:
                    logger.info(f"Successfully extracted {len(extracted_data)} fields for NSN {nsn}")
                    return extracted_data
                else:
                    logger.warning(f"No fields could be extracted for NSN {nsn}")
                    return None
                    
            except TimeoutException:
                logger.warning(f"Timeout on attempt {attempt + 1} for NSN {nsn}")
                if attempt == retry_attempts - 1:
                    logger.error(f"All {retry_attempts} attempts failed for NSN {nsn}")
                    return None
                time.sleep(2)  # Brief pause before retry
                
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1} for NSN {nsn}: {str(e)}")
                if attempt == retry_attempts - 1:
                    return None
                time.sleep(2)
        
        return None

    def _is_nsn_not_found(self, driver, nsn: str) -> bool:
        """
        Check if the NSN was not found on the page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number being checked
            
        Returns:
            True if NSN not found, False otherwise
        """
        try:
            # Look for common "not found" indicators
            not_found_indicators = [
                f"No record of National Stock Number: {nsn}",
                "No records found",
                "NSN not found",
                "No matching records"
            ]
            
            page_source = driver.page_source.lower()
            for indicator in not_found_indicators:
                if indicator.lower() in page_source:
                    logger.info(f"NSN {nsn} not found indicator detected: {indicator}")
                    return True
            
            # Also check for specific DIBBS "no open solicitation" message
            no_open_solicitation = f"No record of National Stock Number: {nsn} with open DIBBS Request For Quotes (RFQ) solicitations."
            if no_open_solicitation.lower() in page_source:
                logger.info(f"NSN {nsn} has no open solicitations")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if NSN {nsn} was found: {str(e)}")
            return False

    def _extract_field(self, driver, field: str, nsn: str) -> Optional[Any]:
        """
        Extract a specific field from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            field: Field name to extract
            nsn: National Stock Number for logging
            
        Returns:
            Extracted field value or None if not found
        """
        try:
            if field == 'amsc_code':
                return self._extract_amsc_code(driver, nsn)
            elif field == 'description':
                return self._extract_description(driver, nsn)
            elif field == 'part_number':
                return self._extract_part_number(driver, nsn)
            elif field == 'manufacturer':
                return self._extract_manufacturer(driver, nsn)
            elif field == 'cage_code':
                return self._extract_cage_code(driver, nsn)
            else:
                logger.warning(f"Unknown field type: {field}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting field {field} for NSN {nsn}: {str(e)}")
            return None

    def _extract_amsc_code(self, driver, nsn: str) -> Optional[str]:
        """
        Extract AMSC code from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            AMSC code string or None if not found
        """
        try:
            # Look for AMSC code in various possible locations
            amsc_selectors = [
                "//td[contains(text(), 'AMSC')]/following-sibling::td",
                "//td[contains(text(), 'AMSC Code')]/following-sibling::td",
                "//span[contains(text(), 'AMSC')]/following-sibling::span",
                "//div[contains(text(), 'AMSC')]/following-sibling::div"
            ]
            
            for selector in amsc_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    amsc_code = element.text.strip()
                    if amsc_code and len(amsc_code) > 0:
                        logger.info(f"AMSC code extracted for NSN {nsn}: {amsc_code}")
                        return amsc_code
                except NoSuchElementException:
                    continue
            
            # Fallback: search page source for AMSC patterns
            page_source = driver.page_source
            import re
            
            # Look for patterns like "AMSC: X" or "AMSC Code: X"
            amsc_patterns = [
                r'AMSC[:\s]+([A-Z])',
                r'AMSC Code[:\s]+([A-Z])',
                r'AMSC\s*=\s*([A-Z])'
            ]
            
            for pattern in amsc_patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    amsc_code = match.group(1).upper()
                    logger.info(f"AMSC code found via pattern for NSN {nsn}: {amsc_code}")
                    return amsc_code
            
            logger.warning(f"AMSC code not found for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting AMSC code for NSN {nsn}: {str(e)}")
            return None

    def _extract_description(self, driver, nsn: str) -> Optional[str]:
        """
        Extract description from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            Description string or None if not found
        """
        try:
            # Look for description in various possible locations
            desc_selectors = [
                "//td[contains(text(), 'Description')]/following-sibling::td",
                "//td[contains(text(), 'Item Name')]/following-sibling::td",
                "//span[contains(text(), 'Description')]/following-sibling::span",
                "//div[contains(text(), 'Description')]/following-sibling::div"
            ]
            
            for selector in desc_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    description = element.text.strip()
                    if description and len(description) > 0:
                        logger.info(f"Description extracted for NSN {nsn}: {description[:100]}...")
                        return description
                except NoSuchElementException:
                    continue
            
            logger.warning(f"Description not found for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting description for NSN {nsn}: {str(e)}")
            return None

    def _extract_part_number(self, driver, nsn: str) -> Optional[str]:
        """
        Extract part number from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            Part number string or None if not found
        """
        try:
            # Look for part number in various possible locations
            part_selectors = [
                "//td[contains(text(), 'Part Number')]/following-sibling::td",
                "//td[contains(text(), 'Part No')]/following-sibling::td",
                "//span[contains(text(), 'Part Number')]/following-sibling::span",
                "//div[contains(text(), 'Part Number')]/following-sibling::div"
            ]
            
            for selector in part_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    part_number = element.text.strip()
                    if part_number and len(part_number) > 0:
                        logger.info(f"Part number extracted for NSN {nsn}: {part_number}")
                        return part_number
                except NoSuchElementException:
                    continue
            
            logger.warning(f"Part number not found for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting part number for NSN {nsn}: {str(e)}")
            return None

    def _extract_manufacturer(self, driver, nsn: str) -> Optional[str]:
        """
        Extract manufacturer from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            Manufacturer string or None if not found
        """
        try:
            # Look for manufacturer in various possible locations
            mfg_selectors = [
                "//td[contains(text(), 'Manufacturer')]/following-sibling::td",
                "//td[contains(text(), 'Mfr')]/following-sibling::td",
                "//span[contains(text(), 'Manufacturer')]/following-sibling::span",
                "//div[contains(text(), 'Manufacturer')]/following-sibling::div"
            ]
            
            for selector in mfg_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    manufacturer = element.text.strip()
                    if manufacturer and len(manufacturer) > 0:
                        logger.info(f"Manufacturer extracted for NSN {nsn}: {manufacturer}")
                        return manufacturer
                except NoSuchElementException:
                    continue
            
            logger.warning(f"Manufacturer not found for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting manufacturer for NSN {nsn}: {str(e)}")
            return None

    def _extract_cage_code(self, driver, nsn: str) -> Optional[str]:
        """
        Extract CAGE code from the NSN page.
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            CAGE code string or None if not found
        """
        try:
            # Look for CAGE code in various possible locations
            cage_selectors = [
                "//td[contains(text(), 'CAGE')]/following-sibling::td",
                "//td[contains(text(), 'CAGE Code')]/following-sibling::td",
                "//span[contains(text(), 'CAGE')]/following-sibling::span",
                "//div[contains(text(), 'CAGE')]/following-sibling::div"
            ]
            
            for selector in cage_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    cage_code = element.text.strip()
                    if cage_code and len(cage_code) > 0:
                        logger.info(f"CAGE code extracted for NSN {nsn}: {cage_code}")
                        return cage_code
                except NoSuchElementException:
                    continue
            
            logger.warning(f"CAGE code not found for NSN {nsn}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting CAGE code for NSN {nsn}: {str(e)}")
            return None

    def _check_closed_solicitation_status(self, driver, nsn: str) -> Optional[bool]:
        """
        Check if the solicitation is closed by looking for specific text patterns.
        
        This method checks for the specific language mentioned in the business logic:
        "No record of National Stock Number: {NSN} with open DIBBS Request For Quotes (RFQ) solicitations."
        
        Args:
            driver: Selenium WebDriver instance
            nsn: National Stock Number for logging
            
        Returns:
            True if closed, False if open, None if unknown
        """
        try:
            page_source = driver.page_source
            
            # Look for the specific closed solicitation pattern
            closed_pattern = f"No record of National Stock Number: {nsn} with open DIBBS Request For Quotes (RFQ) solicitations."
            
            if closed_pattern in page_source:
                logger.info(f"NSN {nsn}: Closed solicitation detected via specific pattern")
                return True
            
            # Look for other indicators of closed solicitations
            closed_indicators = [
                "no open solicitations",
                "no open RFQ solicitations", 
                "no open DIBBS solicitations",
                "solicitation closed",
                "no active solicitations"
            ]
            
            for indicator in closed_indicators:
                if indicator.lower() in page_source.lower():
                    logger.info(f"NSN {nsn}: Closed solicitation detected via indicator: {indicator}")
                    return True
            
            # Look for indicators of open solicitations
            open_indicators = [
                "open solicitations",
                "active solicitations",
                "current solicitations",
                "available solicitations"
            ]
            
            for indicator in open_indicators:
                if indicator.lower() in page_source.lower():
                    logger.info(f"NSN {nsn}: Open solicitation detected via indicator: {indicator}")
                    return False
            
            # If we can't determine, return None (unknown)
            logger.info(f"NSN {nsn}: Solicitation status could not be determined")
            return None
            
        except Exception as e:
            logger.error(f"Error checking closed solicitation status for NSN {nsn}: {str(e)}")
            return None

    def can_apply_to_batch(self) -> bool:
        """This operation can be applied to batches of NSNs."""
        return True

    def apply_to_batch(self, items: List[Any], inputs: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[OperationResult]:
        """
        Apply NSN extraction to a batch of NSNs.
        
        Args:
            items: List of NSNs to process
            inputs: Operation inputs
            context: Shared workflow context
            
        Returns:
            List of OperationResult objects for each NSN
        """
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} NSNs")
        
        for i, nsn in enumerate(items):
            logger.info(f"Processing NSN {i+1}/{total_items}: {nsn}")
            
            # Create inputs for this specific NSN
            nsn_inputs = inputs.copy()
            nsn_inputs['nsn'] = nsn
            
            # Execute extraction for this NSN
            result = self._execute(nsn_inputs, context)
            results.append(result)
            
            # Brief pause between NSNs to avoid overwhelming the server
            if i < total_items - 1:
                time.sleep(1)
        
        # Log batch completion
        successful = len([r for r in results if r.success])
        logger.info(f"Batch processing completed. {successful}/{total_items} successful")
        return results
