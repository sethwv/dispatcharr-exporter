#!/bin/bash
# Package Dispatcharr Prometheus Exporter Plugin

set -e

SRC_DIR="src"
PLUGIN_NAME="dispatcharr_exporter"
OUTPUT_FILE="dispatcharr-exporter.zip"
TEMP_DIR=$(mktemp -d)
VERSION=""

# Verify source directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory not found: $SRC_DIR"
    exit 1
fi

echo "=== Packaging Dispatcharr Prometheus Exporter ==="

# Set dev version if not in CI
if [ -z "$GITHUB_ACTIONS" ]; then
    GIT_HASH=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "00000000")
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    VERSION="-dev-${GIT_HASH}-${TIMESTAMP}"
    
    echo "Version: $VERSION"
    
    # Update version in plugin.py
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$SRC_DIR/plugin.py"
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$SRC_DIR/plugin.py"
    fi
else
    # Extract version from plugin.py (set by workflow)
    VERSION=$(grep -oP '"version": "\K[^"]+' "$SRC_DIR/plugin.py" 2>/dev/null || grep -o '"version": "[^"]*"' "$SRC_DIR/plugin.py" | cut -d'"' -f4)
    echo "Version: $VERSION"
fi

# Clean up old packages
[ -f "$OUTPUT_FILE" ] && rm "$OUTPUT_FILE"
rm -f dispatcharr-exporter-*.zip 2>/dev/null || true

# Copy source to temp dir with plugin name
cp -r "$SRC_DIR" "$TEMP_DIR/$PLUGIN_NAME"

# Create package
echo "Creating package..."
cd "$TEMP_DIR"
zip -q -r "$OLDPWD/$OUTPUT_FILE" "$PLUGIN_NAME" -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store"
cd "$OLDPWD"

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Rename with version
if [ -n "$VERSION" ] && [ "$VERSION" != "dev" ]; then
    VERSIONED_FILE="dispatcharr-exporter-${VERSION}.zip"
    mv "$OUTPUT_FILE" "$VERSIONED_FILE"
    OUTPUT_FILE="$VERSIONED_FILE"
fi

echo "✓ Package created: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
