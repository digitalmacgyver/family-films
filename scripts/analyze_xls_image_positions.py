#!/usr/bin/env python3
"""
Analyze Image Positions in XLS Chapter Sheets

This script examines the actual positions of images in XLS files
to determine which images belong to Start vs End columns.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import subprocess

def analyze_image_positions(xls_file):
    """Analyze where images are positioned in an XLS file"""
    print(f"\n=== ANALYZING {xls_file.name} ===")
    
    # Read the Excel file to understand the structure
    try:
        df = pd.read_excel(xls_file, header=None)
        print(f"Spreadsheet dimensions: {df.shape}")
        
        # Look for header row
        header_row_idx = None
        for idx in range(min(15, len(df))):
            row = df.iloc[idx]
            row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
            if 'start' in row_str and 'title' in row_str:
                header_row_idx = idx
                print(f"Found header row at index {idx}")
                break
        
        if header_row_idx is not None:
            headers = df.iloc[header_row_idx]
            print(f"Headers: {list(headers)}")
            
            # Find Start and End column positions
            start_col = None
            end_col = None
            for i, header in enumerate(headers):
                if pd.notna(header):
                    header_str = str(header).lower().strip()
                    if header_str == 'start':
                        start_col = i
                        print(f"Start column at index {i}")
                    elif header_str == 'end':
                        end_col = i
                        print(f"End column at index {i}")
            
            # Count data rows
            data_rows = 0
            for idx in range(header_row_idx + 1, len(df)):
                row = df.iloc[idx]
                title_cell = row[headers.get('title', 0)] if pd.notna(headers.get('title', 0)) else None
                if pd.notna(title_cell) and str(title_cell).strip():
                    data_rows += 1
            
            print(f"Data rows (chapters): {data_rows}")
            
            return {
                'file': xls_file,
                'header_row': header_row_idx,
                'start_col': start_col,
                'end_col': end_col,
                'data_rows': data_rows
            }
        
    except Exception as e:
        print(f"Error reading {xls_file.name}: {e}")
        return None

def extract_and_examine_images(xls_file, output_dir):
    """Extract images and examine them"""
    print(f"\n=== EXTRACTING IMAGES FROM {xls_file.name} ===")
    
    # Extract images using xls_image_extractor.py
    script_path = Path('/home/viblio/family_films/xls_image_extractor.py')
    
    try:
        result = subprocess.run([
            'python', str(script_path), str(xls_file), '-o', str(output_dir)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Count extracted images
            base_name = xls_file.stem
            extracted_files = []
            
            for i in range(50):  # Check up to 50 images
                image_path = output_dir / f"{base_name}_image_{i:03d}.jpg"
                if image_path.exists():
                    size = image_path.stat().st_size
                    extracted_files.append((image_path, size))
                else:
                    break
            
            print(f"Extracted {len(extracted_files)} images:")
            for image_path, size in extracted_files:
                print(f"  {image_path.name}: {size:,} bytes")
            
            return extracted_files
        else:
            print(f"Extraction failed: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []

def main():
    """Analyze several XLS files to understand image positioning"""
    print("ANALYZING XLS IMAGE POSITIONS")
    
    # Test files with different characteristics
    test_files = [
        "76B-SLD_FROS - Tournament of Roses Cont California Helicopter John and Jonathan in Garden.xls",
        "P-61_FROS - Childrens Fairyland Christmas Disneyland Yosemite with Wrens and Myre relatives.xls", 
        "SLD-07_FROS - Baby Jonathan Plays in Crib and Rose Parade.xls",
        "L-55C_FROS - Bob Lindner Film 4 - Train and Lindners with Earl and Rosabell.xls"
    ]
    
    chapter_sheets_dir = Path('/home/viblio/family_films/chapter_sheets')
    analysis_dir = Path('/tmp/xls_analysis')
    analysis_dir.mkdir(exist_ok=True)
    
    for filename in test_files:
        xls_file = chapter_sheets_dir / filename
        if not xls_file.exists():
            print(f"File not found: {filename}")
            continue
        
        # Analyze spreadsheet structure
        analysis = analyze_image_positions(xls_file)
        
        if analysis:
            # Extract images to examine them
            file_output_dir = analysis_dir / xls_file.stem
            file_output_dir.mkdir(exist_ok=True)
            
            images = extract_and_examine_images(xls_file, file_output_dir)
            
            # Compare analysis
            print(f"\nCOMPARISON for {filename}:")
            print(f"  Chapters expected: {analysis['data_rows']}")
            print(f"  Images extracted: {len(images)}")
            print(f"  Start column: {analysis['start_col']}")
            print(f"  End column: {analysis['end_col']}")
            
            if analysis['start_col'] is not None and analysis['end_col'] is not None:
                expected_images_per_row = 2
                expected_start_images = analysis['data_rows']
                print(f"  Expected total images (2 per row): {expected_images_per_row * analysis['data_rows']}")
                print(f"  Expected Start column images: {expected_start_images}")
                
                # If we have exactly 2x the number of chapters, then likely each row has 2 images
                if len(images) == 2 * analysis['data_rows']:
                    print("  ✓ Likely 2 images per chapter row (Start + End)")
                    print("  → Should use images at indices: 0, 2, 4, 6, 8... for Start column")
                else:
                    print("  ? Unexpected image count - need manual inspection")
            
            print("-" * 80)

if __name__ == "__main__":
    main()