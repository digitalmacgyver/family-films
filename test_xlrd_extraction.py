#!/usr/bin/env python3
"""
Test different XLS image extraction methods
"""
import xlrd
import struct
from pathlib import Path
import os

def extract_with_xlrd_method(xls_file, output_dir):
    """Try extracting images using xlrd with formatting info"""
    print("=== XLRD Method ===")
    
    try:
        # Try with formatting_info=True (only works with .xls files)
        wb = xlrd.open_workbook(xls_file, formatting_info=True)
        print(f"Workbook opened successfully with formatting info")
        print(f"Number of sheets: {wb.nsheets}")
        
        sheet = wb.sheet_by_index(0)
        print(f"Sheet dimensions: {sheet.nrows} rows x {sheet.ncols} cols")
        
        # Check if there's any embedded object info
        if hasattr(wb, 'biff_version'):
            print(f"BIFF version: {wb.biff_version}")
            
    except Exception as e:
        print(f"XLRD method failed: {e}")

def extract_with_ole_method(xls_file, output_dir):
    """Try extracting using OLE compound document parsing"""
    print("\n=== OLE Compound Document Method ===")
    
    try:
        # Try using olefile or similar approach
        with open(xls_file, 'rb') as f:
            content = f.read()
            
        # Look for OLE compound document signature
        if content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            print("✓ Valid OLE compound document detected")
            
            # Look for PNG signatures too (Excel might store PNGs)
            png_start = b'\x89PNG\r\n\x1a\n'
            png_count = 0
            start_pos = 0
            
            while True:
                start_pos = content.find(png_start, start_pos)
                if start_pos == -1:
                    break
                    
                # Try to find end of PNG (IEND chunk)
                iend_marker = b'IEND\xae\x42\x60\x82'
                end_pos = content.find(iend_marker, start_pos)
                if end_pos != -1:
                    end_pos += 8  # Include IEND marker
                    png_data = content[start_pos:end_pos]
                    
                    if len(png_data) > 1024:  # Reasonable size
                        output_file = Path(output_dir) / f"ole_extracted_png_{png_count:03d}.png"
                        with open(output_file, 'wb') as pf:
                            pf.write(png_data)
                        print(f"  ✓ Extracted PNG {png_count}: {len(png_data)} bytes")
                        png_count += 1
                
                start_pos = end_pos if end_pos != -1 else start_pos + 1
                
            print(f"Found {png_count} PNG images")
            
        else:
            print("✗ Not a valid OLE compound document")
            
    except Exception as e:
        print(f"OLE method failed: {e}")

def extract_with_improved_jpeg_method(xls_file, output_dir):
    """Try improved JPEG extraction with better validation"""
    print("\n=== Improved JPEG Method ===")
    
    try:
        with open(xls_file, 'rb') as f:
            content = f.read()
            
        # More comprehensive JPEG signature search
        jpeg_signatures = [
            b'\xff\xd8\xff\xe0',  # Standard JPEG
            b'\xff\xd8\xff\xe1',  # EXIF JPEG
            b'\xff\xd8\xff\xdb',  # JPEG with quantization table
            b'\xff\xd8\xff\xc0',  # JPEG with frame header
        ]
        
        image_count = 0
        
        for sig in jpeg_signatures:
            start_pos = 0
            while True:
                start_pos = content.find(sig, start_pos)
                if start_pos == -1:
                    break
                    
                # Look for end marker
                end_pos = content.find(b'\xff\xd9', start_pos)
                if end_pos != -1:
                    end_pos += 2
                    jpeg_data = content[start_pos:end_pos]
                    
                    # Better size validation
                    if 2048 < len(jpeg_data) < 1024*1024:  # Between 2KB and 1MB
                        output_file = Path(output_dir) / f"improved_jpeg_{image_count:03d}.jpg"
                        with open(output_file, 'wb') as jf:
                            jf.write(jpeg_data)
                            
                        # Try to validate with PIL
                        try:
                            from PIL import Image
                            with Image.open(output_file) as img:
                                w, h = img.size
                                print(f"  ✓ Valid JPEG {image_count}: {w}x{h} ({len(jpeg_data)} bytes)")
                                image_count += 1
                        except Exception:
                            print(f"  ✗ Invalid JPEG data, removing")
                            os.remove(output_file)
                
                start_pos += len(sig)
                
        print(f"Extracted {image_count} valid JPEG images")
        
    except Exception as e:
        print(f"Improved JPEG method failed: {e}")

def main():
    xls_file = "/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls"
    output_dir = "/tmp/extraction_test"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Testing extraction methods on: {os.path.basename(xls_file)}")
    print(f"Output directory: {output_dir}")
    
    extract_with_xlrd_method(xls_file, output_dir)
    extract_with_ole_method(xls_file, output_dir)
    extract_with_improved_jpeg_method(xls_file, output_dir)
    
    print(f"\nFiles created in {output_dir}:")
    for f in sorted(Path(output_dir).glob("*")):
        print(f"  {f.name}")

if __name__ == "__main__":
    main()