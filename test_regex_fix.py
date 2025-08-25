#!/usr/bin/env python3
"""
Test script to verify the regex fix for AMSC extraction.
"""

import re

# Sample HTML content from the debug output
html_content = '''<legend>NSN: <strong>5331-00-618-5361&nbsp; &nbsp;</strong>Nomenclature: <strong>O-RING</strong> &nbsp; &nbsp;AMSC: <strong> T&nbsp; </strong></legend>'''

print("🔍 Testing AMSC extraction regex patterns...")
print(f"HTML content: {html_content}")
print("=" * 60)

# Current pattern (failing)
current_pattern = r'<legend[^>]*>.*?AMSC:\s*<strong>([A-Z])\s*</strong>'
match = re.search(current_pattern, html_content, re.IGNORECASE | re.DOTALL)
print(f"Current pattern: {current_pattern}")
print(f"Match: {match}")
if match:
    print(f"Extracted: '{match.group(1)}'")
else:
    print("❌ No match found")

print()

# Fixed pattern (should work)
fixed_pattern = r'<legend[^>]*>.*?AMSC:\s*<strong>\s*([A-Z])\s*</strong>'
match = re.search(fixed_pattern, html_content, re.IGNORECASE | re.DOTALL)
print(f"Fixed pattern: {fixed_pattern}")
print(f"Match: {match}")
if match:
    print(f"Extracted: '{match.group(1)}'")
else:
    print("❌ No match found")

print()

# Alternative pattern using HTML entity handling
alt_pattern = r'<legend[^>]*>.*?AMSC:\s*<strong>\s*([A-Z])\s*(?:&nbsp;)?\s*</strong>'
match = re.search(alt_pattern, html_content, re.IGNORECASE | re.DOTALL)
print(f"Alternative pattern: {alt_pattern}")
print(f"Match: {match}")
if match:
    print(f"Extracted: '{match.group(1)}'")
else:
    print("❌ No match found")

print()

# Most robust pattern
robust_pattern = r'<legend[^>]*>.*?AMSC:\s*<strong>\s*([A-Z])\s*(?:&nbsp;|\s)*</strong>'
match = re.search(robust_pattern, html_content, re.IGNORECASE | re.DOTALL)
print(f"Robust pattern: {robust_pattern}")
print(f"Match: {match}")
if match:
    print(f"Extracted: '{match.group(1)}'")
else:
    print("❌ No match found")
