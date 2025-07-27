#!/usr/bin/env python3
"""
Comprehensive Excel Management Tool

This script consolidates all Excel-related functionality for the family films project:
- Extract images from XLS files (used by Django import_chapter_metadata command)
- Convert XLS files to XLSX format
- Test and validate image extraction
- Analyze Excel file structure and embedded content
"""

import os
import sys
import argparse
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple, Optional

def extract_images_from_xls(xls_file: str, output_dir: str = None, verbose: bool = True) -> List[str]:
    """
    Extract embedded JPEG images from an XLS file using binary parsing.
    
    This is the core production function used by Django's import_chapter_metadata command.
    
    Args:
        xls_file: Path to the XLS file
        output_dir: Directory to save extracted images (defaults to same directory as XLS file)
        verbose: Whether to print extraction details
    
    Returns:
        List of paths to successfully extracted image files
    """
    if not os.path.exists(xls_file):
        raise FileNotFoundError(f"XLS file not found: {xls_file}")
    
    if output_dir is None:
        output_dir = os.path.dirname(xls_file)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Base name for output files
    base_name = os.path.splitext(os.path.basename(xls_file))[0]
    
    extracted_files = []
    
    try:
        with open(xls_file, 'rb') as f:
            content = f.read()
        
        # JPEG signature markers
        jpeg_start = b'\xff\xd8\xff'
        jpeg_end = b'\xff\xd9'
        
        image_count = 0
        start_pos = 0
        
        if verbose:
            print(f"Analyzing {xls_file} ({len(content):,} bytes)...")
        
        while True:
            # Find next JPEG start marker
            start_pos = content.find(jpeg_start, start_pos)
            if start_pos == -1:
                break
            
            # Find corresponding end marker
            end_pos = content.find(jpeg_end, start_pos)
            if end_pos == -1:
                # If no end marker found, try to estimate based on next start
                next_start = content.find(jpeg_start, start_pos + 1)
                if next_start != -1:
                    end_pos = next_start - 1
                else:
                    # Use rest of file
                    end_pos = len(content)
            else:
                end_pos += 2  # Include the end marker bytes
            
            # Extract potential JPEG data
            jpeg_data = content[start_pos:end_pos]
            
            # Validate image size (reject very small fragments)
            if len(jpeg_data) < 1024:  # Less than 1KB, probably not a real image
                start_pos = end_pos
                continue
            
            # Create output filename
            output_path = os.path.join(output_dir, f"{base_name}_image_{image_count:03d}.jpg")
            
            # Write potential image data
            with open(output_path, 'wb') as img_file:
                img_file.write(jpeg_data)
            
            # Validate with PIL if available
            try:
                from PIL import Image
                with Image.open(output_path) as img:
                    width, height = img.size
                    if verbose:
                        print(f"  ✓ Extracted image {image_count}: {width}x{height} pixels ({len(jpeg_data):,} bytes)")
                        print(f"    Saved to: {output_path}")
                    extracted_files.append(output_path)
                    image_count += 1
            except ImportError:
                # PIL not available, assume it's valid
                if verbose:
                    print(f"  ✓ Extracted image {image_count}: ({len(jpeg_data):,} bytes) - PIL not available for validation")
                    print(f"    Saved to: {output_path}")
                extracted_files.append(output_path)
                image_count += 1
            except Exception as e:
                # Invalid image, remove the file
                if os.path.exists(output_path):
                    os.remove(output_path)
                if verbose:
                    print(f"  ❌ Invalid image data at position {start_pos}: {str(e)}")
            
            # Move to next position
            start_pos = end_pos
        
        if verbose:
            print(f"✅ Extraction complete: {len(extracted_files)} valid images found")
        
        return extracted_files
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract images from {xls_file}: {str(e)}")

def convert_xls_to_xlsx(xls_file: str, output_file: str = None) -> bool:
    """
    Convert XLS file to XLSX format.
    
    Args:
        xls_file: Path to input XLS file
        output_file: Path for output XLSX file (optional)
    
    Returns:
        True if conversion successful, False otherwise
    """
    if not os.path.exists(xls_file):
        raise FileNotFoundError(f"XLS file not found: {xls_file}")
    
    if output_file is None:
        output_file = os.path.splitext(xls_file)[0] + ".xlsx"
    
    try:
        # Try pandas first (most reliable)
        import pandas as pd
        
        print(f"Converting {xls_file} to {output_file} using pandas...")
        
        # Read XLS file
        df = pd.read_excel(xls_file, sheet_name=None, header=None)
        
        # Write to XLSX
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, sheet_df in df.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        print(f"✅ Conversion successful: {output_file}")
        return True
        
    except ImportError:
        print("❌ pandas not available for XLS conversion")
        return False
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        return False

def test_image_extraction(xls_file: str, analysis_mode: bool = False) -> dict:
    """
    Test image extraction from an XLS file and provide analysis.
    
    Args:
        xls_file: Path to XLS file to test
        analysis_mode: If True, provides detailed analysis of extraction pattern
    
    Returns:
        Dictionary with test results and analysis
    """
    if not os.path.exists(xls_file):
        raise FileNotFoundError(f"XLS file not found: {xls_file}")
    
    print(f"=== Testing Image Extraction: {os.path.basename(xls_file)} ===\n")
    
    # Create temporary directory for test extraction
    temp_dir = f"/tmp/excel_test_{os.getpid()}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Extract images
        extracted_images = extract_images_from_xls(xls_file, temp_dir, verbose=True)
        
        results = {
            'file': xls_file,
            'total_images': len(extracted_images),
            'extracted_files': extracted_images,
            'start_images': [],
            'end_images': [],
            'pattern_analysis': {}
        }
        
        if analysis_mode and extracted_images:
            print(f"\n=== Chapter Image Pattern Analysis ===")
            
            # Analyze Start/End pattern (used in production)
            # Even indices (0, 2, 4...) are START images
            # Odd indices (1, 3, 5...) are END images
            start_images = [img for i, img in enumerate(extracted_images) if i % 2 == 0]
            end_images = [img for i, img in enumerate(extracted_images) if i % 2 == 1]
            
            results['start_images'] = start_images
            results['end_images'] = end_images
            
            print(f"Total images found: {len(extracted_images)}")
            print(f"START images (even indices): {len(start_images)}")
            print(f"END images (odd indices): {len(end_images)}")
            
            # Validate 2:1 ratio expected for chapter sheets
            if len(end_images) > 0:
                ratio = len(extracted_images) / len(start_images)
                print(f"Image ratio: {ratio:.1f}:1 (expected 2:1 for chapter sheets)")
                
                if abs(ratio - 2.0) < 0.1:
                    print("✅ Perfect chapter sheet pattern detected")
                    results['pattern_analysis']['pattern_valid'] = True
                else:
                    print("⚠️  Unexpected image ratio - may not be standard chapter sheet")
                    results['pattern_analysis']['pattern_valid'] = False
                    
                results['pattern_analysis']['ratio'] = ratio
            else:
                print("ℹ️  Only one image found - single chapter or different format")
                results['pattern_analysis']['single_image'] = True
            
            print(f"\nSTART column images (for chapter thumbnails):")
            for i, img_path in enumerate(start_images):
                print(f"  Chapter {i+1}: {os.path.basename(img_path)}")
        
        return results
        
    finally:
        # Cleanup temporary files
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def analyze_excel_structure(file_path: str) -> dict:
    """
    Analyze the structure of an Excel file for chapter sheet format.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        Dictionary with structure analysis
    """
    print(f"=== Analyzing Excel Structure: {os.path.basename(file_path)} ===\n")
    
    try:
        import pandas as pd
        
        # Read without headers to see raw structure
        df = pd.read_excel(file_path, header=None)
        
        analysis = {
            'file': file_path,
            'dimensions': df.shape,
            'film_id': None,
            'headers': {},
            'data_rows': 0
        }
        
        print(f"File dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
        
        # Extract film ID from A3 (row 2, column 0)
        if df.shape[0] > 2:
            film_id = str(df.iloc[2, 0]) if not pd.isna(df.iloc[2, 0]) else ''
            analysis['film_id'] = film_id.strip()
            print(f"Film ID (A3): {analysis['film_id']}")
        
        # Find header row (typically row 9, index 8)
        header_row_idx = None
        for idx in range(min(15, df.shape[0])):  # Check first 15 rows
            row = df.iloc[idx]
            if any(str(cell).lower().strip() in ['start', 'end', 'title'] for cell in row if pd.notna(cell)):
                header_row_idx = idx
                break
        
        if header_row_idx is not None:
            headers = df.iloc[header_row_idx]
            analysis['header_row'] = header_row_idx + 1  # 1-based for Excel
            analysis['headers'] = {col: str(val).strip() for col, val in enumerate(headers) if pd.notna(val)}
            
            print(f"Header row found at row {header_row_idx + 1}:")
            for col, header in analysis['headers'].items():
                print(f"  Column {chr(65 + col)}: {header}")
            
            # Count data rows
            data_rows = 0
            for idx in range(header_row_idx + 1, df.shape[0]):
                row = df.iloc[idx]
                if not row.isna().all():  # Not completely empty
                    data_rows += 1
            
            analysis['data_rows'] = data_rows
            print(f"Data rows: {data_rows}")
            
            # Estimate chapters
            if 'start' in [h.lower() for h in analysis['headers'].values()]:
                print(f"Estimated chapters: {data_rows}")
                print(f"Expected images: {data_rows * 2} (Start + End columns)")
        
        return analysis
        
    except ImportError:
        print("❌ pandas not available for structure analysis")
        return {'error': 'pandas not available'}
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return {'error': str(e)}

def batch_process_chapter_sheets(chapter_sheets_dir: str = None, test_mode: bool = True):
    """
    Process all XLS files in the chapter_sheets directory.
    
    Args:
        chapter_sheets_dir: Path to chapter sheets directory
        test_mode: If True, only analyzes without extracting images
    """
    if chapter_sheets_dir is None:
        chapter_sheets_dir = "/home/viblio/family_films/chapter_sheets"
    
    if not os.path.exists(chapter_sheets_dir):
        print(f"❌ Chapter sheets directory not found: {chapter_sheets_dir}")
        return
    
    xls_files = list(Path(chapter_sheets_dir).glob("*.xls"))
    print(f"=== Batch Processing {len(xls_files)} XLS Files ===\n")
    
    if not xls_files:
        print("No XLS files found in chapter sheets directory")
        return
    
    results = []
    
    for xls_file in xls_files:
        print(f"Processing: {xls_file.name}")
        
        try:
            if test_mode:
                # Analyze structure only
                result = analyze_excel_structure(str(xls_file))
                result['analysis_only'] = True
            else:
                # Full image extraction test
                result = test_image_extraction(str(xls_file), analysis_mode=True)
            
            results.append(result)
            print("✅ Success\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            results.append({'file': str(xls_file), 'error': str(e)})
    
    # Summary
    print("=== Batch Processing Summary ===")
    successful = len([r for r in results if 'error' not in r])
    failed = len(results) - successful
    
    print(f"Processed: {len(results)} files")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if not test_mode:
        total_images = sum(r.get('total_images', 0) for r in results if 'total_images' in r)
        print(f"Total images found: {total_images}")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Excel management tool')
    parser.add_argument('command', choices=['extract-images', 'convert-xlsx', 'test-extraction', 
                                           'analyze-structure', 'batch-process'],
                        help='Command to run')
    parser.add_argument('--file', help='Excel file to process')
    parser.add_argument('--output-dir', help='Output directory for extracted images')
    parser.add_argument('--output-file', help='Output file for conversions')
    parser.add_argument('--chapter-sheets-dir', default='/home/viblio/family_films/chapter_sheets',
                        help='Directory containing chapter sheet files')
    parser.add_argument('--analysis-mode', action='store_true',
                        help='Provide detailed pattern analysis')
    parser.add_argument('--extract-mode', action='store_true',
                        help='Actually extract images (not just analyze)')
    
    args = parser.parse_args()
    
    if args.command == 'extract-images':
        if not args.file:
            print("ERROR: --file required for extract-images command")
            sys.exit(1)
        
        output_dir = args.output_dir or os.path.dirname(args.file)
        extracted = extract_images_from_xls(args.file, output_dir)
        print(f"\n✅ Extracted {len(extracted)} images to {output_dir}")
        
    elif args.command == 'convert-xlsx':
        if not args.file:
            print("ERROR: --file required for convert-xlsx command")
            sys.exit(1)
        
        success = convert_xls_to_xlsx(args.file, args.output_file)
        if not success:
            sys.exit(1)
            
    elif args.command == 'test-extraction':
        if not args.file:
            print("ERROR: --file required for test-extraction command")
            sys.exit(1)
        
        results = test_image_extraction(args.file, args.analysis_mode)
        print(f"\n✅ Test complete - found {results['total_images']} images")
        
    elif args.command == 'analyze-structure':
        if not args.file:
            print("ERROR: --file required for analyze-structure command")
            sys.exit(1)
        
        analysis = analyze_excel_structure(args.file)
        if 'error' not in analysis:
            print(f"\n✅ Analysis complete - {analysis['data_rows']} data rows found")
        else:
            print(f"\n❌ Analysis failed: {analysis['error']}")
            sys.exit(1)
            
    elif args.command == 'batch-process':
        test_mode = not args.extract_mode
        batch_process_chapter_sheets(args.chapter_sheets_dir, test_mode)

if __name__ == '__main__':
    main()