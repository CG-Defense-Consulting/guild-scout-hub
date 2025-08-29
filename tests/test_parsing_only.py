#!/usr/bin/env python3
"""
Quick test script for DIBBS text file parsing operation only.
Tests with the existing IN250827.TXT file.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.operations.dibbs_text_file_parsing_operation import DibbsTextFileParsingOperation
from utils.logger import setup_logger

def test_parsing_only():
    """Test just the parsing operation with existing file."""
    
    # Setup logging
    logger = setup_logger(__name__)
    logger.setLevel(logging.INFO)
    
    # Get the path to the existing test file
    test_file_path = Path("../downloads/IN250827.TXT")
    
    if not test_file_path.exists():
        logger.error(f"Test file not found: {test_file_path}")
        return False
    
    logger.info(f"🧪 Testing DIBBS parsing with existing file: {test_file_path}")
    logger.info(f"File size: {test_file_path.stat().st_size / 1024:.1f} KB")
    
    try:
        # Create the parsing operation
        parsing_op = DibbsTextFileParsingOperation()
        
        # Execute the parsing operation
        logger.info("🚀 Executing parsing operation...")
        result = parsing_op._execute({
            'file_path': str(test_file_path),
            'encoding': 'utf-8',
            'errors': 'ignore'
        }, {})
        
        # Check the result
        if result.success:
            logger.info("✅ Parsing operation completed successfully!")
            
            # Get the data
            parsed_rows = result.data.get('parsed_rows', [])
            structured_data = result.data.get('structured_data', [])
            
            logger.info(f"📊 Parsing Results:")
            logger.info(f"  - Raw parsed rows: {len(parsed_rows)}")
            logger.info(f"  - Structured data: {len(structured_data)}")
            logger.info(f"  - Metadata: {result.metadata}")
            
            # Show some sample data
            if structured_data:
                logger.info("\n📋 Sample structured data (first 3 records):")
                for i, record in enumerate(structured_data[:3]):
                    logger.info(f"  Record {i+1}:")
                    logger.info(f"    - Solicitation: {record.get('solicitation_number', 'N/A')}")
                    logger.info(f"    - NSN: {record.get('national_stock_number', 'N/A')}")
                    logger.info(f"    - PRN: {record.get('purchase_request_number', 'N/A')}")
                    logger.info(f"    - Date: {record.get('return_by_date', 'N/A')}")
                    logger.info(f"    - Qty: {record.get('quantity', 'N/A')}")
                    logger.info(f"    - Unit: {record.get('unit_type', 'N/A')} ({record.get('unit_type_long', 'N/A')})")
                    logger.info(f"    - Item: {record.get('item', 'N/A')}")
                    logger.info(f"    - Description: {record.get('description', 'N/A')}")
                    logger.info(f"    - Raw: {record.get('raw_row', 'N/A')[:100]}...")
                    logger.info("")
            
            return True
            
        else:
            logger.error(f"❌ Parsing operation failed: {result.error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exception during testing: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main entry point."""
    print("🧪 DIBBS Text File Parsing Test (Parsing Only)")
    print("=" * 50)
    
    success = test_parsing_only()
    
    if success:
        print("\n🎉 Parsing test completed successfully!")
        print("The parsing operation is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Parsing test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
