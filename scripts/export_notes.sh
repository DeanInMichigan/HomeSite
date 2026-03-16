#!/bin/bash
# export_notes.sh — Export recipes from Apple Notes to ~/notes_export/
#
# Usage: bash scripts/export_notes.sh [folder-name]
# Default folder name: Recipes

FOLDER_NAME="${1:-Recipes}"
EXPORT_DIR="$HOME/notes_export"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Exporting notes from folder: \"$FOLDER_NAME\""
echo "Output directory: $EXPORT_DIR"
echo ""

rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"

osascript "$SCRIPT_DIR/export_notes.applescript" "$FOLDER_NAME" "$EXPORT_DIR/"

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Export failed (exit code $EXIT_CODE)."
    echo "Make sure:"
    echo "  1. Your Notes folder is named exactly: $FOLDER_NAME"
    echo "  2. Terminal has Automation permission for Notes"
    echo "     System Settings > Privacy & Security > Automation"
    exit 1
fi

echo ""
echo "Done! Contents of $EXPORT_DIR:"
ls "$EXPORT_DIR"
