#!/usr/bin/env python3
"""
Extract chapter thumbnails from all Excel files in chapter_sheets directory
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from django.core.management import call_command

def main():
    """Extract thumbnails from all Excel files"""
    chapter_sheets_dir = Path('chapter_sheets')
    
    if not chapter_sheets_dir.exists():
        print(f"Directory not found: {chapter_sheets_dir}")
        return 1
    
    # Find all Excel files
    xls_files = list(chapter_sheets_dir.glob('*.xls'))
    xlsx_files = list(chapter_sheets_dir.glob('*.xlsx'))
    
    all_files = sorted(xls_files + xlsx_files)
    
    print(f"Found {len(all_files)} Excel files to process")
    print(f"  - {len(xls_files)} .xls files (will use binary image extraction)")
    print(f"  - {len(xlsx_files)} .xlsx files (will use openpyxl image extraction)")
    print()
    
    success_count = 0
    error_count = 0
    
    for excel_file in all_files:
        try:
            print(f"Processing: {excel_file.name}")
            
            # Run the import command for this file
            call_command(
                'import_chapter_metadata', 
                file=excel_file.name,
                save_thumbnails='media/chapter_thumbnails',
                verbosity=1
            )
            
            success_count += 1
            print(f"✓ Successfully processed {excel_file.name}\n")
            
        except Exception as e:
            print(f"✗ Error processing {excel_file.name}: {str(e)}\n")
            error_count += 1
            continue
    
    print("=" * 60)
    print(f"Thumbnail extraction completed!")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total files: {len(all_files)}")
    
    if error_count > 0:
        print(f"\nNote: {error_count} files had errors. Check the output above for details.")
    
    print(f"\nThumbnails saved to: media/chapter_thumbnails/")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())