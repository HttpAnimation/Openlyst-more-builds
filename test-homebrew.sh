#!/bin/bash

# Test script for Homebrew tap building
# This script tests the build_homebrew_tap.py script locally

set -e

echo "🧪 Testing Homebrew Tap Builder"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required dependencies are installed
print_status "Checking dependencies..."
pip3 show requests > /dev/null 2>&1 || {
    print_warning "Installing requests..."
    pip3 install requests
}

# Test directory setup
TEST_DIR="test-homebrew-tap"
print_status "Setting up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

# Test macOS build
print_status "Testing macOS Homebrew tap generation..."
if python3 build_homebrew_tap.py --output-dir "$TEST_DIR/macos" --platform macOS --verbose; then
    print_status "✅ macOS build completed successfully"
    
    # Check if Formula directory exists
    if [ -d "$TEST_DIR/macos/Formula" ]; then
        FORMULA_COUNT=$(find "$TEST_DIR/macos/Formula" -name "*.rb" | wc -l)
        print_status "Generated $FORMULA_COUNT macOS formulae"
        
        # Show first formula as example
        if [ "$FORMULA_COUNT" -gt 0 ]; then
            FIRST_FORMULA=$(find "$TEST_DIR/macos/Formula" -name "*.rb" | head -1)
            print_status "Sample formula: $(basename "$FIRST_FORMULA")"
            echo "----------------------------------------"
            head -20 "$FIRST_FORMULA"
            echo "----------------------------------------"
        fi
    else
        print_warning "Formula directory not found"
    fi
    
    # Check tap info
    if [ -f "$TEST_DIR/macos/tap-info.json" ]; then
        print_status "Tap info generated:"
        cat "$TEST_DIR/macos/tap-info.json"
    fi
else
    print_error "❌ macOS build failed"
fi

echo ""

# Test Linux build
print_status "Testing Linux Homebrew tap generation..."
if python3 build_homebrew_tap.py --output-dir "$TEST_DIR/linux" --platform Linux --verbose; then
    print_status "✅ Linux build completed successfully"
    
    # Check if Formula directory exists
    if [ -d "$TEST_DIR/linux/Formula" ]; then
        FORMULA_COUNT=$(find "$TEST_DIR/linux/Formula" -name "*.rb" | wc -l)
        print_status "Generated $FORMULA_COUNT Linux formulae"
        
        # Show first formula as example
        if [ "$FORMULA_COUNT" -gt 0 ]; then
            FIRST_FORMULA=$(find "$TEST_DIR/linux/Formula" -name "*.rb" | head -1)
            print_status "Sample formula: $(basename "$FIRST_FORMULA")"
            echo "----------------------------------------"
            head -20 "$FIRST_FORMULA"
            echo "----------------------------------------"
        fi
    else
        print_warning "Formula directory not found"
    fi
    
    # Check tap info
    if [ -f "$TEST_DIR/linux/tap-info.json" ]; then
        print_status "Tap info generated:"
        cat "$TEST_DIR/linux/tap-info.json"
    fi
else
    print_error "❌ Linux build failed"
fi

echo ""

# Validate generated formulae
print_status "Validating generated formulae..."

validate_formula() {
    local formula_file="$1"
    local platform="$2"
    
    if [ ! -f "$formula_file" ]; then
        return 1
    fi
    
    # Check for basic Ruby syntax
    if grep -q "class\|cask" "$formula_file" && \
       grep -q "url\|version\|desc" "$formula_file"; then
        print_status "✅ $platform formula $(basename "$formula_file") appears valid"
        return 0
    else
        print_warning "⚠️ $platform formula $(basename "$formula_file") might have issues"
        return 1
    fi
}

# Validate a few formulae from each platform
if [ -d "$TEST_DIR/macos/Formula" ]; then
    find "$TEST_DIR/macos/Formula" -name "*.rb" | head -3 | while read formula; do
        validate_formula "$formula" "macOS"
    done
fi

if [ -d "$TEST_DIR/linux/Formula" ]; then
    find "$TEST_DIR/linux/Formula" -name "*.rb" | head -3 | while read formula; do
        validate_formula "$formula" "Linux"
    done
fi

# Summary
echo ""
print_status "🎉 Test Summary"
print_status "==============="

if [ -d "$TEST_DIR/macos" ]; then
    MACOS_COUNT=$(find "$TEST_DIR/macos/Formula" -name "*.rb" 2>/dev/null | wc -l)
    print_status "macOS formulae generated: $MACOS_COUNT"
fi

if [ -d "$TEST_DIR/linux" ]; then
    LINUX_COUNT=$(find "$TEST_DIR/linux/Formula" -name "*.rb" 2>/dev/null | wc -l)
    print_status "Linux formulae generated: $LINUX_COUNT"
fi

print_status "Test output saved in: $TEST_DIR/"
print_status "You can inspect the generated formulae manually"

echo ""
print_status "🚀 To deploy to production:"
print_status "1. Commit the build_homebrew_tap.py script"
print_status "2. Run the 'Build Homebrew Tap' GitHub Action workflow"
print_status "3. The formulae will be committed to the homebrew-tap/ directory"

# Optional cleanup
read -p "Clean up test directory? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEST_DIR"
    print_status "Test directory cleaned up"
fi