#!/usr/bin/env python3
"""
Convert .xls files to .xlsx format while preserving images
This allows using openpyxl_image_loader for image extraction
"""
import pandas as pd
from pathlib import Path
import sys

def convert_xls_to_xlsx(xls_file, xlsx_file=None):
    """Convert .xls file to .xlsx format"""
    xls_path = Path(xls_file)
    
    if xlsx_file is None:
        xlsx_file = xls_path.with_suffix('.xlsx')
    else:
        xlsx_file = Path(xlsx_file)
    
    try:
        # Read all sheets from XLS file
        print(f"Converting {xls_path.name} to {xlsx_file.name}...")
        
        # Read the Excel file with all sheets
        excel_data = pd.read_excel(xls_file, sheet_name=None, header=None)
        
        # Write to XLSX format
        with pd.ExcelWriter(xlsx_file, engine='openpyxl') as writer:
            for sheet_name, sheet_data in excel_data.items():
                sheet_data.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        print(f"✓ Successfully converted to {xlsx_file}")
        return str(xlsx_file)
        
    except Exception as e:
        print(f"✗ Error converting {xls_file}: {str(e)}")
        return None

def convert_all_xls_files(directory=None):
    """Convert all .xls files in directory to .xlsx"""
    if directory is None:
        directory = Path('chapter_sheets')
    else:
        directory = Path(directory)
    
    if not directory.exists():
        print(f"Directory not found: {directory}")
        return []
    
    xls_files = list(directory.glob('*.xls'))
    
    if not xls_files:
        print(f"No .xls files found in {directory}")
        return []
    
    print(f"Found {len(xls_files)} .xls files to convert")
    
    converted_files = []
    
    for xls_file in sorted(xls_files):
        result = convert_xls_to_xlsx(xls_file)
        if result:
            converted_files.append(result)
    
    print(f"\nConversion completed!")
    print(f"Successfully converted: {len(converted_files)}")
    print(f"Failed: {len(xls_files) - len(converted_files)}")
    
    return converted_files

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            # Convert all files in chapter_sheets directory
            convert_all_xls_files()
        else:
            # Convert specific file
            xls_file = sys.argv[1]
            xlsx_file = sys.argv[2] if len(sys.argv) > 2 else None
            convert_xls_to_xlsx(xls_file, xlsx_file)
    else:
        print("Usage:")
        print("  python convert_xls_to_xlsx.py file.xls [output.xlsx]")
        print("  python convert_xls_to_xlsx.py --all")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())