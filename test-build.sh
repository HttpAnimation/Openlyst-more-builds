#!/usr/bin/env bash
# Local development script to test the AltStore builder

set -e

echo "🔨 AltStore Builder - Local Test"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Run the builder
echo ""
echo "🏗️  Building AltStore repository..."
python3 build_altstore_repo.py \
    --output-dir repo \
    --repo-url https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo
    --verbose

# Validate output
echo ""
echo "✅ Validation"
echo "============"

if [ -f "repo/apps.json" ]; then
    echo "✓ apps.json exists"
    
    # Validate JSON syntax
    if python3 -c "import json; json.load(open('repo/apps.json'))" 2>/dev/null; then
        echo "✓ JSON is valid"
    else
        echo "✗ JSON validation failed"
        exit 1
    fi
    
    # Count apps
    app_count=$(python3 -c "import json; print(len(json.load(open('repo/apps.json')).get('apps', [])))")
    echo "✓ Repository contains $app_count apps"
    
    # Show file size
    file_size=$(du -h repo/apps.json | cut -f1)
    echo "✓ Repository size: $file_size"
else
    echo "✗ apps.json not found"
    exit 1
fi

if [ -f "repo/index.json" ]; then
    echo "✓ index.json exists"
else
    echo "✗ index.json not found"
    exit 1
fi

echo ""
echo "🎉 Build successful!"
echo ""
echo "📝 Next steps:"
echo "  1. Review repo/apps.json"
echo "  2. Commit changes: git add repo/ && git commit -m 'build: update altstore repository'"
echo "  3. Push to GitHub: git push"
echo ""
