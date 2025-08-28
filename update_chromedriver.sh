#!/bin/bash

# ChromeDriver Update Script for macOS
# This script updates ChromeDriver to the latest version compatible with your Chrome browser

set -e  # Exit on any error

echo "🚀 ChromeDriver Update Script for macOS"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS. Current OS: $OSTYPE"
    exit 1
fi

# Check if Chrome is installed
if ! command -v "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" &> /dev/null; then
    print_error "Google Chrome is not installed or not found in the expected location"
    print_status "Please install Google Chrome first: https://www.google.com/chrome/"
    exit 1
fi

# Get Chrome version
print_status "Detecting Chrome version..."
CHROME_VERSION=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

if [ -z "$CHROME_VERSION" ]; then
    print_error "Could not determine Chrome version"
    exit 1
fi

print_success "Chrome version detected: $CHROME_VERSION"

# Get the major version number
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1)
print_status "Chrome major version: $CHROME_MAJOR_VERSION"

# Try to get the ChromeDriver version that matches our Chrome major version
print_status "Searching for ChromeDriver version compatible with Chrome $CHROME_MAJOR_VERSION..."

CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR_VERSION")

# Check if we got a valid version (not an XML error)
if [[ "$CHROMEDRIVER_VERSION" == *"<?xml"* ]] || [[ "$CHROMEDRIVER_VERSION" == *"Error"* ]] || [ -z "$CHROMEDRIVER_VERSION" ]; then
    print_warning "No specific ChromeDriver version found for Chrome $CHROME_MAJOR_VERSION, trying previous versions..."
    
    # Try previous major versions (e.g., 138, 137, 136...)
    for version in $(seq $((CHROME_MAJOR_VERSION-1)) -1 $((CHROME_MAJOR_VERSION-10))); do
        print_status "Trying ChromeDriver for Chrome version $version..."
        CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$version")
        
        if [[ "$CHROMEDRIVER_VERSION" != *"<?xml"* ]] && [[ "$CHROMEDRIVER_VERSION" != *"Error"* ]] && [ -n "$CHROMEDRIVER_VERSION" ]; then
            print_success "Found compatible ChromeDriver version: $CHROMEDRIVER_VERSION (for Chrome $version)"
            break
        fi
    done
    
    # If still no version found, fall back to the latest
    if [[ "$CHROMEDRIVER_VERSION" == *"<?xml"* ]] || [[ "$CHROMEDRIVER_VERSION" == *"Error"* ]] || [ -z "$CHROMEDRIVER_VERSION" ]; then
        print_warning "No compatible version found, falling back to latest ChromeDriver..."
        CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
        print_status "Latest available ChromeDriver version: $CHROMEDRIVER_VERSION"
    fi
else
    print_success "Found ChromeDriver version for Chrome $CHROME_MAJOR_VERSION: $CHROMEDRIVER_VERSION"
fi

# Check if we already have this version
if command -v chromedriver &> /dev/null; then
    CURRENT_VERSION=$(chromedriver --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ "$CURRENT_VERSION" = "$CHROMEDRIVER_VERSION" ]; then
        print_success "ChromeDriver is already up to date (version $CURRENT_VERSION)"
        print_status "Current ChromeDriver location: $(which chromedriver)"
        chromedriver --version
        exit 0
    else
        print_status "Current ChromeDriver version: $CURRENT_VERSION"
        print_status "Updating to version: $CHROMEDRIVER_VERSION"
    fi
fi

# Create temporary directory for download
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

print_status "Downloading ChromeDriver version $CHROMEDRIVER_VERSION..."

# Download ChromeDriver for macOS
if curl -L -o "chromedriver_mac64.zip" "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_mac64.zip"; then
    print_success "Download completed successfully"
else
    print_error "Failed to download ChromeDriver"
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Verify download
if [ ! -f "chromedriver_mac64.zip" ]; then
    print_error "Downloaded file not found"
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

print_status "Downloaded file size: $(ls -lh chromedriver_mac64.zip | awk '{print $5}')"

# Extract ChromeDriver
print_status "Extracting ChromeDriver..."
unzip -q chromedriver_mac64.zip

if [ ! -f "chromedriver" ]; then
    print_error "ChromeDriver executable not found in downloaded archive"
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Make executable
chmod +x chromedriver

# Test the downloaded ChromeDriver
print_status "Testing downloaded ChromeDriver..."
if ./chromedriver --version > /dev/null 2>&1; then
    print_success "Downloaded ChromeDriver is working correctly"
    ./chromedriver --version
else
    print_error "Downloaded ChromeDriver is not working"
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Backup existing ChromeDriver if it exists
if command -v chromedriver &> /dev/null; then
    EXISTING_PATH=$(which chromedriver)
    if [ -n "$EXISTING_PATH" ]; then
        print_status "Backing up existing ChromeDriver..."
        sudo mv "$EXISTING_PATH" "${EXISTING_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
        print_success "Existing ChromeDriver backed up"
    fi
fi

# Install new ChromeDriver
print_status "Installing new ChromeDriver..."

# Try to install to /usr/local/bin first (requires sudo)
if sudo mv chromedriver /usr/local/bin/ 2>/dev/null; then
    INSTALL_PATH="/usr/local/bin/chromedriver"
    print_success "ChromeDriver installed to $INSTALL_PATH"
else
    # Fall back to user's home directory
    INSTALL_PATH="$HOME/bin/chromedriver"
    mkdir -p "$HOME/bin"
    mv chromedriver "$INSTALL_PATH"
    print_success "ChromeDriver installed to $INSTALL_PATH"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        print_status "Adding $HOME/bin to PATH..."
        echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
        echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bash_profile"
        print_success "PATH updated. Please restart your terminal or run: source ~/.zshrc"
    fi
fi

# Clean up
cd - > /dev/null
rm -rf "$TEMP_DIR"

# Verify installation
print_status "Verifying installation..."
if command -v chromedriver &> /dev/null; then
    print_success "ChromeDriver installation verified!"
    print_status "Location: $(which chromedriver)"
    print_status "Version: $(chromedriver --version)"
    
    # Test functionality
    if chromedriver --version > /dev/null 2>&1; then
        print_success "ChromeDriver is working correctly!"
    else
        print_error "ChromeDriver installation may have issues"
        exit 1
    fi
else
    print_error "ChromeDriver not found in PATH after installation"
    print_status "Please check the installation path: $INSTALL_PATH"
    exit 1
fi

echo ""
print_success "ChromeDriver update completed successfully!"
print_status "You can now use ChromeDriver in your Python scripts and workflows."
echo ""
print_status "If you installed to $HOME/bin, you may need to restart your terminal"
print_status "or run: source ~/.zshrc (or ~/.bash_profile)"
