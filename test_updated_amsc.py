#!/usr/bin/env python3
"""
Quick test script to verify the updated AMSC extraction operation.
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import the ETL modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_updated_amsc_extraction():
    """Test the updated AMSC extraction operation."""
    
    print("🧪 Testing updated AMSC extraction operation...")
    print("=" * 50)
    
    try:
        from etl.core.operations import AmscExtractionOperation
        
        # Create the operation
        amsc_extraction = AmscExtractionOperation()
        print("✅ AMSC extraction operation created successfully")
        
        # Test HTML content (from our debug output)
        test_html = '''<legend>NSN: <strong>5331-00-618-5361&nbsp; &nbsp;</strong>Nomenclature: <strong>O-RING</strong> &nbsp; &nbsp;AMSC: <strong> T&nbsp; </strong></legend>'''
        
        print(f"📄 Test HTML: {test_html}")
        print(f"📏 HTML length: {len(test_html)} characters")
        
        # Execute the extraction
        result = amsc_extraction.execute(
            inputs={'html_content': test_html, 'nsn': '5331006185361'},
            context={}
        )
        
        print(f"\n🔍 Extraction result:")
        print(f"   Success: {result.success}")
        print(f"   Status: {result.status}")
        print(f"   Error: {result.error}")
        
        if result.success:
            amsc_code = result.data.get('amsc_code')
            print(f"   AMSC Code: '{amsc_code}'")
            
            if amsc_code == 'T':
                print("🎯 SUCCESS: Expected AMSC 'T' was extracted correctly!")
            else:
                print(f"⚠️ WARNING: Expected 'T' but got '{amsc_code}'")
        else:
            print("❌ Extraction failed")
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_amsc_extraction()
