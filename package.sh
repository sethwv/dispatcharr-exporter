#!/bin/bash
# Package Dispatcharr Prometheus Exporter Plugin for Web UI Import

echo "=== Packaging Dispatcharr Prometheus Exporter Plugin ==="
echo ""

# Plugin directory
PLUGIN_DIR="prometheus_exporter"
OUTPUT_FILE="prometheus_exporter.zip"

# Check if plugin directory exists
if [ ! -d "$PLUGIN_DIR" ]; then
    echo "Error: Plugin directory not found: $PLUGIN_DIR"
    exit 1
fi

# Remove old package if exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "Removing existing package..."
    rm "$OUTPUT_FILE"
fi

# Create zip package
echo "Creating package: $OUTPUT_FILE"
zip -r "$OUTPUT_FILE" "$PLUGIN_DIR" -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store"

if [ $? -eq 0 ]; then
    echo ""
    echo "=== Package Created Successfully! ==="
    echo ""
    echo "File: $OUTPUT_FILE"
    echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo ""
    echo "Installation steps:"
    echo "1. Open your Dispatcharr web UI"
    echo "2. Navigate to the Plugins page"
    echo "3. Click the 'Import' button"
    echo "4. Upload $OUTPUT_FILE"
    echo "5. Enable the plugin and configure settings"
    echo ""
else
    echo "Error: Failed to create package"
    exit 1
fi
