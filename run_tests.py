#!/usr/bin/env python3
"""
Test Runner Script

This script runs the workflow integration tests from the project root.
It's a convenient way to test that all workflows are working correctly.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the workflow integration tests."""
    print("🚀 Workflow Integration Test Runner")
    print("=" * 40)
    
    # Check if we're in the project root
    if not Path("etl").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   (where the 'etl' folder is located)")
        sys.exit(1)
    
    # Run the tests
    try:
        result = subprocess.run([
            sys.executable, "tests/run_workflow_tests.py"
        ], check=False)
        
        print()
        print("=" * 40)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print("🎉 Your workflows are working correctly")
        else:
            print("❌ Some tests failed")
            print("🔍 Check the output above for details")
            print("\n💡 Tips:")
            print("   - Make sure all dependencies are installed")
            print("   - Check that the ETL directory structure is correct")
            print("   - Run individual tests to debug specific issues")
        
        return result.returncode
        
    except FileNotFoundError:
        print("❌ Error: Test runner not found")
        print("   Make sure 'tests/run_workflow_tests.py' exists")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
