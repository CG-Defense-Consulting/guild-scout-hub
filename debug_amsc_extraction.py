#!/usr/bin/env python3
"""
Temporary debugging script for AMSC extraction.
This script will be deleted after debugging is complete.

Purpose: Navigate to NSN 5331006185361, extract HTML, and save it for analysis.
Expected AMSC: T
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the project root to the path so we can import the ETL modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_amsc_extraction():
    """Debug AMSC extraction for NSN 5331006185361."""
    
    print("🔍 Starting AMSC extraction debugging for NSN: 5331006185361")
    print("Expected AMSC: T")
    print("=" * 60)
    
    try:
        # Import required operations
        from etl.core.operations import (
            ChromeSetupOperation,
            ConsentPageOperation,
            NsnPageNavigationOperation,
            ClosedSolicitationCheckOperation,
            AmscExtractionOperation
        )
        
        print("✅ Successfully imported all required operations")
        
        # Step 1: Setup Chrome
        print("\n🚀 Step 1: Setting up Chrome...")
        chrome_setup = ChromeSetupOperation(headless=True)  # Set to True for headless operation
        chrome_result = chrome_setup.execute(inputs={}, context={})
        
        if not chrome_result.success:
            print(f"❌ Chrome setup failed: {chrome_result.error}")
            return
        
        chrome_driver = chrome_result.data.get('driver')
        if not chrome_driver:
            print("❌ Chrome driver not found in result")
            return
        
        print("✅ Chrome setup successful")
        
        # Step 2: Navigate to NSN page
        print("\n🚀 Step 2: Navigating to NSN page...")
        nsn_navigation = NsnPageNavigationOperation()
        nav_result = nsn_navigation.execute(
            inputs={'nsn': '5331006185361', 'chrome_driver': chrome_driver, 'timeout': 30, 'retry_attempts': 3},
            context={'chrome_driver': chrome_driver}
        )
        
        if not nav_result.success:
            print(f"❌ Navigation failed: {nav_result.error}")
            return
        
        print("✅ Navigation successful")
        
        # Step 3: Handle consent page (if present)
        print("\n🚀 Step 3: Handling consent page...")
        consent_page = ConsentPageOperation()
        consent_result = consent_page.execute(
            inputs={'nsn': '5331006185361', 'timeout': 30, 'retry_attempts': 3},
            context={'chrome_driver': chrome_driver}
        )
        
        if consent_result.success:
            print("✅ Consent page handled successfully")
        else:
            print(f"⚠️ Consent page handling failed: {consent_result.error}")
        
        # Step 4: Get the current page HTML content
        print("\n🚀 Step 4: Extracting HTML content...")
        html_content = chrome_driver.page_source
        
        print(f"✅ HTML content extracted (length: {len(html_content)} characters)")
        
        # Step 5: Check if solicitation is closed
        print("\n🚀 Step 5: Checking if solicitation is closed...")
        closed_check = ClosedSolicitationCheckOperation()
        closed_result = closed_check.execute(
            inputs={'html_content': html_content, 'nsn': '5331006185361'},
            context={}
        )
        
        if closed_result.success:
            is_closed = closed_result.data.get('is_closed')
            print(f"✅ Closed status check: {is_closed}")
            
            if is_closed:
                print("ℹ️ Solicitation is closed, skipping AMSC extraction")
                return
        else:
            print(f"❌ Closed status check failed: {closed_result.error}")
        
        # Step 6: Extract AMSC code
        print("\n🚀 Step 6: Extracting AMSC code...")
        amsc_extraction = AmscExtractionOperation()
        amsc_result = amsc_extraction.execute(
            inputs={'html_content': html_content, 'nsn': '5331006185361'},
            context={}
        )
        
        if amsc_result.success:
            amsc_code = amsc_result.data.get('amsc_code')
            print(f"✅ AMSC extraction successful: '{amsc_code}'")
            
            if amsc_code == 'T':
                print("🎯 SUCCESS: Expected AMSC 'T' was extracted correctly!")
            else:
                print(f"⚠️ WARNING: Expected 'T' but got '{amsc_code}'")
        else:
            print(f"❌ AMSC extraction failed: {amsc_result.error}")
        
        # Step 7: Save HTML content for debugging
        print("\n🚀 Step 7: Saving HTML content for debugging...")
        
        # Create debug directory if it doesn't exist
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        # Save HTML content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = debug_dir / f"nsn_5331006185361_html_{timestamp}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML content saved to: {html_filename}")
        
        # Save debug info as JSON
        debug_info = {
            'nsn': '5331006185361',
            'expected_amsc': 'T',
            'timestamp': timestamp,
            'html_filename': str(html_filename),
            'html_length': len(html_content),
            'chrome_setup_success': chrome_result.success,
            'navigation_success': nav_result.success,
            'consent_handling_success': consent_result.success,
            'closed_status_check_success': closed_result.success,
            'closed_status': closed_result.data.get('is_closed') if closed_result.success else None,
            'amsc_extraction_success': amsc_result.success,
            'extracted_amsc': amsc_result.data.get('amsc_code') if amsc_result.success else None,
            'amsc_extraction_error': amsc_result.error if not amsc_result.success else None
        }
        
        json_filename = debug_dir / f"nsn_5331006185361_debug_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, indent=2)
        
        print(f"✅ Debug info saved to: {json_filename}")
        
        # Step 8: Display current page title and URL for context
        print("\n🚀 Step 8: Page context information...")
        print(f"Current URL: {chrome_driver.current_url}")
        print(f"Page Title: {chrome_driver.title}")
        
        # Step 9: Look for AMSC-related text in HTML (simple search)
        print("\n🚀 Step 9: Searching for AMSC-related text in HTML...")
        
        # Look for common AMSC patterns
        amsc_patterns = [
            'AMSC:',
            'AMSC :',
            'AMSC',
            'T',
            'legend'
        ]
        
        for pattern in amsc_patterns:
            if pattern in html_content:
                # Find the context around the pattern
                index = html_content.find(pattern)
                start = max(0, index - 100)
                end = min(len(html_content), index + 100)
                context = html_content[start:end]
                
                print(f"✅ Found '{pattern}' in HTML context:")
                print(f"   Context: ...{context}...")
                print()
            else:
                print(f"❌ Pattern '{pattern}' not found in HTML")
        
        # Step 10: Test the cleaner approach - clean HTML then simple regex
        print("\n🚀 Step 10: Testing cleaner approach (clean HTML + simple regex)...")
        
        # Clean the HTML by removing HTML entities and tags
        import re
        cleaned_html = html_content
        
        # Replace HTML entities
        cleaned_html = cleaned_html.replace('&nbsp;', ' ')
        cleaned_html = cleaned_html.replace('&amp;', '&')
        cleaned_html = cleaned_html.replace('&lt;', '<')
        cleaned_html = cleaned_html.replace('&gt;', '>')
        
        # Remove HTML tags
        cleaned_html = re.sub(r'<[^>]+>', '', cleaned_html)
        
        # Remove extra whitespace
        cleaned_html = re.sub(r'\s+', ' ', cleaned_html).strip()
        
        print(f"✅ Cleaned HTML length: {len(cleaned_html)} characters")
        print(f"✅ Cleaned HTML preview: {cleaned_html[:200]}...")
        
        # Now apply simple regex to find AMSC
        amsc_simple_pattern = r'AMSC:\s*([A-Z])'
        match = re.search(amsc_simple_pattern, cleaned_html, re.IGNORECASE)
        
        if match:
            amsc_code = match.group(1).upper()
            print(f"🎯 SUCCESS: Clean approach extracted AMSC: '{amsc_code}'")
            
            if amsc_code == 'T':
                print("🎯 PERFECT: Expected AMSC 'T' was extracted correctly!")
            else:
                print(f"⚠️ WARNING: Expected 'T' but got '{amsc_code}'")
        else:
            print("❌ Clean approach failed to extract AMSC")
            
            # Show the relevant part of cleaned HTML
            amsc_index = cleaned_html.find('AMSC:')
            if amsc_index != -1:
                start = max(0, amsc_index - 50)
                end = min(len(cleaned_html), amsc_index + 100)
                context = cleaned_html[start:end]
                print(f"   Context around AMSC: {context}")
        
        print("=" * 60)
        print("🔍 Debugging complete! Check the debug_output directory for saved files.")
        
    except Exception as e:
        print(f"❌ Debugging failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            if 'chrome_driver' in locals() and chrome_driver:
                print("\n🧹 Cleaning up Chrome driver...")
                chrome_driver.quit()
                print("✅ Chrome driver cleaned up")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")

if __name__ == "__main__":
    debug_amsc_extraction()
