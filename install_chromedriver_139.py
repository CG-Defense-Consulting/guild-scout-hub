#!/usr/bin/env python3
"""
ChromeDriver 139 Compatibility Installer

This script uses webdriver-manager to automatically download and install
the correct ChromeDriver version compatible with Chrome 139.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        sys.exit(1)
    
    return result

def install_webdriver_manager():
    """Install webdriver-manager if not already installed."""
    try:
        import webdriver_manager
        print("✅ webdriver-manager already installed")
        return True
    except ImportError:
        print("Installing webdriver-manager...")
        run_command("pip install webdriver-manager")
        return True

def get_chrome_version():
    """Get the current Chrome version."""
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    if not os.path.exists(chrome_path):
        print("❌ Google Chrome not found at expected location")
        return None
    
    try:
        result = subprocess.run([chrome_path, "--version"], 
                              capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        print(f"✅ Chrome version: {version}")
        return version
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get Chrome version: {e}")
        return None

def install_chromedriver_with_manager():
    """Use webdriver-manager to install the correct ChromeDriver."""
    print("\n🚀 Installing ChromeDriver using webdriver-manager...")
    
    # Create a Python script to use webdriver-manager
    script_content = '''
import os
import sys
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

print("🔍 Detecting Chrome version and downloading compatible ChromeDriver...")

try:
    # This will automatically download the correct ChromeDriver version
    driver_path = ChromeDriverManager().install()
    print(f"✅ ChromeDriver downloaded to: {driver_path}")
    
    # Test the installation
    print("🧪 Testing ChromeDriver installation...")
    service = Service(driver_path)
    
    # Try to create a driver instance (this will fail if incompatible)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ ChromeDriver test successful!")
    
    # Get version info
    driver_version = driver.capabilities['browserVersion']
    print(f"✅ Chrome version detected: {driver_version}")
    
    driver.quit()
    
    # Copy to a standard location
    import shutil
    target_path = "/usr/local/bin/chromedriver"
    
    try:
        # Backup existing if it exists
        if os.path.exists(target_path):
            backup_path = f"{target_path}.backup"
            shutil.move(target_path, backup_path)
            print(f"✅ Existing ChromeDriver backed up to: {backup_path}")
        
        # Copy new ChromeDriver
        shutil.copy2(driver_path, target_path)
        os.chmod(target_path, 0o755)  # Make executable
        print(f"✅ ChromeDriver installed to: {target_path}")
        
        # Verify installation
        result = subprocess.run([target_path, "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Installation verified: {result.stdout.strip()}")
        
    except Exception as e:
        print(f"⚠️ Could not install to /usr/local/bin: {e}")
        print(f"✅ ChromeDriver is available at: {driver_path}")
        print("   You can add this path to your PATH environment variable")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
'''
    
    # Write the script to a temporary file
    script_path = "temp_chromedriver_install.py"
    with open(script_path, "w") as f:
        f.write(script_content)
    
    try:
        # Run the script
        print("📝 Running ChromeDriver installation script...")
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        
        if result.stderr:
            print(f"⚠️ Warnings: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    finally:
        # Clean up
        if os.path.exists(script_path):
            os.remove(script_path)

def main():
    """Main installation function."""
    print("🚀 ChromeDriver 139 Compatibility Installer")
    print("=" * 50)
    
    # Check if we're on macOS
    if sys.platform != "darwin":
        print("❌ This script is designed for macOS")
        sys.exit(1)
    
    # Get Chrome version
    chrome_version = get_chrome_version()
    if not chrome_version:
        print("❌ Could not determine Chrome version")
        sys.exit(1)
    
    # Check if Chrome 139
    if "139" not in chrome_version:
        print(f"⚠️ Warning: Chrome version {chrome_version} detected")
        print("   This script is designed for Chrome 139")
        print("   It may still work, but compatibility is not guaranteed")
    
    # Install webdriver-manager
    install_webdriver_manager()
    
    # Install ChromeDriver
    install_chromedriver_with_manager()
    
    print("\n🎉 ChromeDriver installation completed!")
    print("\n📋 Next steps:")
    print("   1. Test ChromeDriver: chromedriver --version")
    print("   2. If installed to /usr/local/bin, it should work immediately")
    print("   3. If installed elsewhere, add the path to your PATH variable")
    print("   4. Restart your terminal if needed")

if __name__ == "__main__":
    main()
