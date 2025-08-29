#!/usr/bin/env python3
"""
DIBBS Text File Parsing Operation

This operation parses the index.txt file downloaded from DIBBS using the correct parsing logic
for the DIBBS format. It extracts solicitation numbers, NSNs, purchase request numbers,
dates, quantities, unit types, and descriptions from the fixed-width text format.
"""

import logging
import os
import re
from typing import Dict, Any, List, Optional
from .base_operation import BaseOperation, OperationResult, OperationStatus

logger = logging.getLogger(__name__)

# Unit type mapping for parsing
UNIT_TYPE_MAPPING = {
    'AM': 'AMPOULE',
    'AT': 'ASSORTMENT',
    'AY': 'ASSEMBLY',
    'BA': 'BALL',
    'BD': 'BUNDLE',
    'BE': 'BALE',
    'BF': 'BOARD FOOT',
    'BG': 'BAG',
    'BK': 'BOOK',
    'BL': 'BARREL',
    'BO': 'BOLT',
    'BR': 'BAR',
    'BT': 'BOTTLE',
    'BX': 'BOX',
    'CA': 'CARTRIDGE',
    'CB': 'CARBOY',
    'CD': 'CUBIC YARD',
    'CE': 'CONE',
    'CF': 'CUBIC FOOT',
    'CK': 'CAKE',
    'CL': 'COIL',
    'CM': 'CENTIMETER',
    'CN': 'CAN',
    'CO': 'CONTAINER',
    'CS': 'CASE',
    'CT': 'CARTON',
    'CU': 'CUBE',
    'CY': 'CYLINDER',
    'CZ': 'CUBIC METER',
    'DR': 'DRUM',
    'DZ': 'DOZEN',
    'EA': 'EACH',
    'EN': 'ENVELOPE',
    'FT': 'FOOT',
    'FV': 'FIVE',
    'FY': 'FIFTY',
    'GL': 'GALLON',
    'GP': 'GROUP',
    'GR': 'GROSS',
    'HD': 'HUNDRED (100)',
    'HK': 'HANK',
    'IN': 'INCH',
    'JR': 'JAR',
    'KG': 'KILOGRAM',
    'KT': 'KIT',
    'LB': 'POUND',
    'LG': 'LENGTH',
    'LI': 'LITER',
    'LT': 'LOT',
    'MC': 'THOUSAND CUBIC FEET',
    'ME': 'MEAL',
    'MM': 'MILLIMETER',
    'MR': 'METER',
    'MX': 'THOUSAND (1000)',
    'OT': 'OUTFIT',
    'OZ': 'OUNCE',
    'PD': 'PAD',
    'PG': 'PACKAGE',
    'PK': 'PACKAGE BUY',
    'PM': 'PLATE',
    'PR': 'PAIR',
    'PT': 'PINT',
    'PZ': 'PACKET',
    'QT': 'QUART',
    'RA': 'RATION',
    'RL': 'REEL',
    'RM': 'REAM (500 SHEETS)',
    'RO': 'ROLL',
    'SD': 'SKID',
    'SE': 'SET',
    'SF': 'SQUARE FOOT',
    'SH': 'SHEET',
    'SK': 'SKIEN',
    'SL': 'SPOOL',
    'SO': 'SHOT',
    'SP': 'STRIP',
    'SV': 'SERVICE',
    'SX': 'STICK',
    'SY': 'SQUARE YARD',
    'TD': 'TWENTY-FOUR',
    'TE': 'TEN',
    'TF': 'TWENTY-FIVE',
    'TN': 'TON',
    'TO': 'TROY OUNCE',
    'TS': 'THIRTY-SIX',
    'TU': 'TUBE',
    'VI': 'VIAL',
    'XX': 'DOLLARS FOR SERVICES',
    'YD': 'YARD'
}

class DibbsTextFileParsingOperation(BaseOperation):
    """
    Operation that parses DIBBS index.txt files using the correct parsing logic.
    
    This operation:
    1. Reads the downloaded index.txt file
    2. Combines multi-line records (each logical record is split across 2 physical lines)
    3. Parses fixed-width fields based on DIBBS format specifications
    4. Extracts all relevant data fields including solicitation numbers, NSNs, PRNs, dates, quantities, etc.
    5. Returns structured data ready for database upload
    """
    
    def __init__(self):
        """Initialize the DIBBS text file parsing operation."""
        super().__init__(
            name="dibbs_text_file_parsing",
            description="Parse DIBBS index.txt files using correct format specifications"
        )
        
        # Set required inputs
        self.set_required_inputs(['file_path'])
        
        # Set optional inputs
        self.set_optional_inputs(['encoding', 'errors'])
    
    def _execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> OperationResult:
        """
        Execute the DIBBS text file parsing operation.
        
        Args:
            inputs: Operation inputs containing 'file_path' and optionally 'encoding' and 'errors'
            context: Shared workflow context
            
        Returns:
            OperationResult with parsed data and metadata
        """
        try:
            file_path = inputs['file_path']
            encoding = inputs.get('encoding', 'utf-8')
            errors = inputs.get('errors', 'ignore')
            
            logger.info(f"Parsing DIBBS index file: {file_path}")
            
            # Parse the file
            parsed_data = self._parse_index_file(file_path, encoding, errors)
            
            if not parsed_data:
                return OperationResult(
                    success=True,
                    status=OperationStatus.COMPLETED,
                    data={'parsed_rows': [], 'total_records': 0},
                    metadata={'message': 'No data parsed from index file'}
                )
            
            # Prepare structured data for database upload
            structured_data = self._prepare_structured_data(parsed_data)
            
            logger.info(f"Successfully parsed {len(parsed_data)} rows from index file")
            
            return OperationResult(
                success=True,
                status=OperationStatus.COMPLETED,
                data={
                    'parsed_rows': parsed_data,
                    'structured_data': structured_data,
                    'total_records': len(parsed_data)
                },
                metadata={
                    'file_path': file_path,
                    'encoding_used': encoding,
                    'parsing_method': 'fixed_width_dibbs_format'
                }
            )
            
        except Exception as e:
            error_msg = f"DIBBS text file parsing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return OperationResult(
                success=False,
                status=OperationStatus.FAILED,
                error=error_msg
            )
    
    def _parse_index_file(self, file_path: str, encoding: str = 'utf-8', errors: str = 'ignore') -> List[List[str]]:
        """
        Parse the index.txt file using the correct parsing logic for DIBBS format.
        
        Real format analysis shows each line is 140 characters with this structure:
        SOLICITATION(13) + NSN(13) + SPACES + PRN(10) + DATE(8) + PDF_NAME + SPACES + QTY(7) + UNIT(2) + DESCRIPTION + CODES
        
        Args:
            file_path: Path to the downloaded index.txt file
            encoding: File encoding to use
            errors: How to handle encoding errors
            
        Returns:
            List of parsed rows with extracted data
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Index file not found: {file_path}")
            
            parsed_rows = []
            
            with open(file_path, 'r', encoding=encoding, errors=errors) as f:
                lines = f.readlines()
            
            logger.info(f"Read {len(lines)} lines from index file")
            
            # Combine multi-line records (each logical record is split across 2 physical lines)
            combined_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Check if this line contains a solicitation number pattern (starts with SPE and is 13 chars)
                if line.startswith('SPE') and len(line) >= 13:
                    # This is the start of a record, try to combine with next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('SPE'):
                            # Combine the two lines
                            combined_line = line + next_line
                            combined_lines.append(combined_line)
                            i += 2  # Skip both lines
                            continue
                        else:
                            # Single line record
                            combined_lines.append(line)
                            i += 1
                            continue
                    else:
                        # Last line, single record
                        combined_lines.append(line)
                        i += 1
                        continue
                else:
                    # Skip lines that don't start with SPE
                    i += 1
                    continue
            
            # If no records were found with the SPE pattern, try alternative patterns
            if not combined_lines:
                logger.warning("No SPE-pattern records found, trying alternative parsing approaches...")
                
                # Debug: Log the first few lines to understand the file format
                logger.info(f"First 5 lines of file for debugging:")
                for i, line in enumerate(lines[:5]):
                    logger.info(f"  Line {i+1}: '{line.strip()}' (length: {len(line.strip())})")
                
                # Look for any lines that contain .pdf (which should indicate RFQ data)
                pdf_lines = [line.strip() for line in lines if '.pdf' in line]
                if pdf_lines:
                    logger.info(f"Found {len(pdf_lines)} lines with .pdf, attempting direct parsing")
                    combined_lines = pdf_lines
                else:
                    # Look for lines with typical RFQ patterns (numbers, dates, etc.)
                    potential_rfq_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 20:  # Reasonable length for RFQ data
                            # Check if line contains typical RFQ elements
                            if any(pattern in line for pattern in ['/', '.pdf', 'SPE', 'DLA', 'MIL']):
                                potential_rfq_lines.append(line)
                    
                    if potential_rfq_lines:
                        logger.info(f"Found {len(potential_rfq_lines)} potential RFQ lines")
                        combined_lines = potential_rfq_lines
                    else:
                        logger.warning("No recognizable RFQ data patterns found in file")
                        # Debug: Log all lines to understand what we're working with
                        logger.info("All lines in file for debugging:")
                        for i, line in enumerate(lines):
                            if line.strip():  # Only log non-empty lines
                                logger.info(f"  Line {i+1}: '{line.strip()}' (length: {len(line.strip())})")
            
            logger.info(f"Combined into {len(combined_lines)} logical records")
            
            for line_num, line in enumerate(combined_lines, 1):
                try:
                    # Each combined line should be approximately 140 characters (allowing for some variation)
                    if len(line) < 100:  # Minimum reasonable length for a complete record
                        logger.warning(f"Line {line_num}: Too short ({len(line)} chars), skipping")
                        continue
                    
                    # Parse based on fixed positions
                    solicitation_number = line[0:13].strip()  # Positions 0-12
                    national_stock_number = line[13:26].strip()  # Positions 13-25
                    
                    # Find the PRN and date after the spaces
                    # Look for the pattern: spaces + 10 digits + 8 digits (mm/dd/yy)
                    prn_date_match = re.search(r'\s+(\d{10})(\d{2}/\d{2}/\d{2})', line)
                    if not prn_date_match:
                        logger.warning(f"Line {line_num}: Could not find PRN/date pattern, skipping")
                        continue
                    
                    purchase_request_number = prn_date_match.group(1)
                    return_by_date_raw = prn_date_match.group(2)
                    
                    # Convert date from mm/dd/yy format to YYYY-mm-dd format
                    try:
                        from datetime import datetime
                        # Parse the mm/dd/yy date
                        date_obj = datetime.strptime(return_by_date_raw, '%m/%d/%y')
                        # Format as YYYY-mm-dd
                        return_by_date = date_obj.strftime('%Y-%m-%d')
                        logger.debug(f"Date converted: {return_by_date_raw} -> {return_by_date}")
                    except Exception as e:
                        logger.warning(f"Could not convert date {return_by_date_raw}: {e}, using original format")
                        return_by_date = return_by_date_raw
                    
                    # Find quantity and unit after .pdf
                    if '.pdf' not in line:
                        logger.warning(f"Line {line_num}: No .pdf found, skipping")
                        continue
                    
                    # Split by .pdf and get the description part
                    parts = line.split('.pdf')
                    if len(parts) != 2:
                        logger.warning(f"Line {line_num}: Invalid .pdf split, skipping")
                        continue
                    
                    description_part = parts[1].strip()
                    
                    # Extract quantity (7 digits) and unit (2 letters)
                    qty_unit_match = re.search(r'(\d{7})([A-Z]{2})', description_part)
                    if not qty_unit_match:
                        logger.warning(f"Line {line_num}: Could not find quantity/unit pattern, skipping")
                        continue
                    
                    quantity_str = qty_unit_match.group(1)
                    unit_type = qty_unit_match.group(2)
                    
                    # Convert quantity to integer, removing leading zeros
                    quantity = int(quantity_str.lstrip('0') or '0')
                    
                    # Get unit type description
                    unit_type_long = UNIT_TYPE_MAPPING.get(unit_type, 'Unknown')
                    
                    # Extract description (everything after unit type)
                    description_start = description_part.find(unit_type) + 2
                    description = description_part[description_start:].strip()
                    
                    # The description format is: ITEM+DESCRIPTION(20 chars) + SPACE(1) + ALPHANUMERIC_CODE(9-12 chars)
                    # Extract the first 20 characters for item + description
                    if len(description) >= 21:  # At least 20 chars + 1 space + some code
                        item_description_part = description[:20].strip()
                        # The remaining part after 20 chars + 1 space is the alphanumeric code
                        alphanumeric_code = description[21:].strip()
                    else:
                        item_description_part = description
                        alphanumeric_code = ''
                    
                    # Split item_description_part into item and additional description
                    if ',' in item_description_part:
                        item, *additional_desc = item_description_part.split(',')
                        additional_description = ','.join(additional_desc).strip()
                    else:
                        item = item_description_part
                        additional_description = ''
                    
                    parsed_row = [
                        solicitation_number,
                        national_stock_number,
                        purchase_request_number,
                        return_by_date,
                        quantity,
                        unit_type,
                        unit_type_long,
                        item,
                        additional_description,
                        alphanumeric_code,  # Add the alphanumeric code as a separate field
                        line  # raw row
                    ]
                    
                    parsed_rows.append(parsed_row)
                    logger.debug(f"Line {line_num}: Parsed successfully - SN: {solicitation_number}, NSN: {national_stock_number}, QTY: {quantity}, UNIT: {unit_type}")
                    
                except Exception as e:
                    logger.warning(f"Line {line_num}: Parsing error: {str(e)}, skipping")
                    continue
            
            logger.info(f"Successfully parsed {len(parsed_rows)} rows from index file")
            return parsed_rows
            
        except Exception as e:
            logger.error(f"Error parsing index file: {str(e)}")
            raise
    
    def _prepare_structured_data(self, parsed_data: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Prepare parsed data in structured format for database upload.
        
        Args:
            parsed_data: List of parsed rows from the index file
            
        Returns:
            List of dictionaries with structured data ready for database upload
        """
        structured_data = []
        
        for row in parsed_data:
            structured_row = {
                'solicitation_number': row[0],
                'national_stock_number': row[1],
                'purchase_request_number': row[2],
                'return_by_date': row[3],
                'quantity': row[4],
                'unit_type': row[5],
                'unit_type_long': row[6],
                'item': row[7],
                'description': row[8],
                'alphanumeric_code': row[9],
                'raw_row': row[10]
            }
            structured_data.append(structured_row)
        
        return structured_data
    
    def can_apply_to_batch(self) -> bool:
        """
        DIBBS text file parsing can be applied to batches.
        
        Returns:
            True - this operation supports batch processing
        """
        return True
    
    def apply_to_batch(self, items: List[Any], inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[OperationResult]:
        """
        Apply DIBBS text file parsing to a batch of items.
        
        Args:
            items: List of file paths to process
            inputs: Dictionary of inputs for this operation
            context: Optional context data shared across operations
            
        Returns:
            List of OperationResult for each item
        """
        if context is None:
            context = {}
        
        results = []
        total_items = len(items)
        
        logger.info(f"Processing batch of {total_items} files for DIBBS text file parsing")
        
        for i, file_path in enumerate(items, 1):
            logger.info(f"Processing file {i}/{total_items}: {file_path}")
            
            # Create item-specific inputs
            item_inputs = inputs.copy()
            item_inputs['file_path'] = file_path
            
            # Execute operation for this item
            result = self.execute(item_inputs, context)
            results.append(result)
        
        logger.info(f"Batch processing completed. {len([r for r in results if r.success])}/{total_items} successful")
        return results
