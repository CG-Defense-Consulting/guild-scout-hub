#!/usr/bin/env python3
"""
Workflow Test Runner

This script runs the workflow integration tests to verify that all workflows
are working correctly without actually uploading to Supabase.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run the workflow integration tests."""
    print("🚀 Starting Workflow Integration Tests")
    print("=" * 50)
    
    # Get the project root
    project_root = Path(__file__).parent.parent
    etl_path = project_root / "etl"
    
    print(f"Project root: {project_root}")
    print(f"ETL path: {etl_path}")
    print()
    
    # Check if we're in the right directory
    if not etl_path.exists():
        print("❌ Error: ETL directory not found. Please run this from the project root.")
        sys.exit(1)
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ Pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ Error: Pytest not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
            print("✅ Pytest installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install pytest")
            sys.exit(1)
    
    # Set up environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DIBBS_DOWNLOAD_DIR"] = "./test_downloads"
    os.environ["LOG_FILE"] = "./test_logs/test.log"
    os.environ["VITE_SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_key"
    
    print("🔧 Environment variables set for testing")
    print()
    
    # Run the tests
    print("🧪 Running workflow integration tests...")
    print()
    
    try:
        # Run pytest with the test file
        test_file = Path(__file__).parent / "test_workflow_integration.py"
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], cwd=project_root)
        
        print()
        print("=" * 50)
        
        if result.returncode == 0:
            print("✅ All tests passed successfully!")
            print("🎉 Workflows are working correctly")
        else:
            print("❌ Some tests failed")
            print("🔍 Check the output above for details")
            
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/test_workflow_integration.py::{test_name}", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], cwd=project_root)
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = main()
    
    sys.exit(exit_code)
