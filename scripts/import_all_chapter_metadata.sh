#!/bin/bash

# Script to import metadata from all Excel files in chapter_sheets directory

echo "Starting import of chapter metadata from Excel files..."
echo "============================================="
echo ""

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the import command for all files
echo "Running import command..."
python manage.py import_chapter_metadata

echo ""
echo "============================================="
echo "Import complete!"
echo ""
echo "Note: To extract thumbnail images from the Excel files, they need to be"
echo "converted from .xls to .xlsx format. The metadata has been imported"
echo "successfully, but thumbnails could not be extracted from .xls files."
echo ""
echo "To import a single file, use:"
echo "python manage.py import_chapter_metadata --file 'filename.xls'"
echo ""
echo "To run in dry-run mode (no database changes), add --dry-run flag"