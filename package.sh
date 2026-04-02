#!/bin/bash
# Package Dispatcharr Plugin
#
# Plugin name and output filename are derived entirely from src/plugin.json,
# so this script requires no plugin-specific edits.
#
# Dispatcharr 0.19.0 Compatibility:
# - The src/ folder contains the plugin source code
# - src/plugin.json contains the plugin manifest
# - The build process packages src/ as {slug}/ inside the zip

set -e

SRC_DIR="src"
TEMP_DIR=$(mktemp -d)
VERSION=""
EXPLICIT_VERSION=""

# Parse arguments
# Usage: ./package.sh [--version X.Y.Z | -v X.Y.Z]
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version|-v)
            EXPLICIT_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--version X.Y.Z]"
            exit 1
            ;;
    esac
done

# Verify source directory and plugin.json exist
if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory not found: $SRC_DIR"
    exit 1
fi

if [ ! -f "$SRC_DIR/plugin.json" ]; then
    echo "Error: plugin.json not found in $SRC_DIR"
    echo "This is required for Dispatcharr 0.19.0 compatibility"
    exit 1
fi

# Derive plugin slug and display name from plugin.json
PLUGIN_DISPLAY=$(python3 -c "import json; print(json.load(open('$SRC_DIR/plugin.json'))['name'])")
PLUGIN_NAME=$(echo "$PLUGIN_DISPLAY" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

# Derive output base name (underscores → hyphens)
OUTPUT_BASE="${PLUGIN_NAME//_/-}"
OUTPUT_FILE="${OUTPUT_BASE}.zip"

echo "=== Packaging ${PLUGIN_DISPLAY} ==="

# Set version
if [ -n "$EXPLICIT_VERSION" ]; then
    VERSION="$EXPLICIT_VERSION"
    echo "Version: $VERSION (explicit)"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$SRC_DIR/plugin.json"
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$SRC_DIR/plugin.json"
    fi
elif [ -z "$GITHUB_ACTIONS" ]; then
    GIT_HASH=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "00000000")
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    VERSION="-dev-${GIT_HASH}-${TIMESTAMP}"

    echo "Version: $VERSION"
else
    # Extract version from plugin.json (set by workflow)
    VERSION=$(grep -oP '"version": "\K[^"]+' "$SRC_DIR/plugin.json" 2>/dev/null || grep -o '"version": "[^"]*"' "$SRC_DIR/plugin.json" | cut -d'"' -f4)
    echo "Version: $VERSION"
fi

# Clean up old packages
[ -f "$OUTPUT_FILE" ] && rm "$OUTPUT_FILE"
rm -f "${OUTPUT_BASE}"-*.zip 2>/dev/null || true

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
    # Strip leading dash from version for filename
    FILE_VERSION="${VERSION#-}"
    VERSIONED_FILE="${OUTPUT_BASE}-${FILE_VERSION}.zip"
    mv "$OUTPUT_FILE" "$VERSIONED_FILE"
    OUTPUT_FILE="$VERSIONED_FILE"
fi

echo "✓ Package created: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
