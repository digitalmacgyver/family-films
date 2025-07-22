#!/usr/bin/env python3
"""
Advanced test for XLS image extraction using multiple approaches
"""

import os
import sys
import struct

def extract_images_from_xls_binary(xls_file):
    """Try to extract images from XLS file by parsing binary data"""
    print(f"\n=== Binary extraction attempt from {os.path.basename(xls_file)} ===")
    
    try:
        with open(xls_file, 'rb') as f:
            content = f.read()
        
        # Look for JPEG signatures and try to extract
        jpeg_signature = b'\xff\xd8\xff'
        jpeg_end = b'\xff\xd9'
        
        images_found = 0
        start_pos = 0
        
        while True:
            # Find next JPEG start
            start_pos = content.find(jpeg_signature, start_pos)
            if start_pos == -1:
                break
            
            # Find corresponding end
            end_pos = content.find(jpeg_end, start_pos)
            if end_pos == -1:
                # Try to find next start to estimate end
                next_start = content.find(jpeg_signature, start_pos + 1)
                if next_start != -1:
                    end_pos = next_start - 1
                else:
                    end_pos = len(content)
            else:
                end_pos += 2  # Include the end marker
            
            # Extract potential JPEG data
            jpeg_data = content[start_pos:end_pos]
            
            # Basic validation - JPEG should be at least 1KB
            if len(jpeg_data) > 1024:
                output_path = f"/home/viblio/family_films/binary_extracted_image_{images_found}.jpg"
                with open(output_path, 'wb') as img_file:
                    img_file.write(jpeg_data)
                
                print(f"  Extracted potential JPEG ({len(jpeg_data)} bytes) to {output_path}")
                
                # Try to validate with PIL
                try:
                    from PIL import Image
                    img = Image.open(output_path)
                    print(f"    ✓ Valid image: {img.size[0]}x{img.size[1]} pixels")
                    images_found += 1
                except Exception as e:
                    print(f"    ✗ Invalid image data: {e}")
                    os.remove(output_path)  # Clean up invalid file
            
            start_pos = end_pos
        
        print(f"Total valid images extracted: {images_found}")
        return images_found > 0
        
    except Exception as e:
        print(f"Error in binary extraction: {e}")
        return False

def test_xls2xlsx_conversion(xls_file):
    """Test xls2xlsx library for conversion"""
    print(f"\n=== Testing xls2xlsx conversion ===")
    
    try:
        import xls2xlsx
        
        output_file = xls_file.replace('.xls', '_xls2xlsx.xlsx')
        print(f"Converting {os.path.basename(xls_file)} to {os.path.basename(output_file)}")
        
        # Convert
        result = xls2xlsx.to_xlsx(xls_file, output_file)
        print(f"Conversion result: {result}")
        
        if os.path.exists(output_file):
            print(f"✓ Conversion successful")
            
            # Check for images in converted file
            import openpyxl
            from openpyxl_image_loader import SheetImageLoader
            
            wb = openpyxl.load_workbook(output_file)
            images_found = 0
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                print(f"\nChecking sheet '{sheet_name}':")
                
                # Method 1: _images attribute
                if hasattr(sheet, '_images') and sheet._images:
                    print(f"  Found {len(sheet._images)} images via _images")
                    for i, img in enumerate(sheet._images):
                        try:
                            if hasattr(img, '_data'):
                                img_data = img._data()
                                output_path = f"/home/viblio/family_films/xls2xlsx_extracted_{sheet_name}_{i}.png"
                                with open(output_path, 'wb') as f:
                                    f.write(img_data)
                                print(f"    ✓ Saved image {i} to {output_path}")
                                images_found += 1
                            elif hasattr(img, 'path'):
                                print(f"    Image {i} path: {img.path}")
                            else:
                                print(f"    Image {i} attributes: {dir(img)}")
                        except Exception as e:
                            print(f"    Error with image {i}: {e}")
                
                # Method 2: Image loader
                try:
                    image_loader = SheetImageLoader(sheet)
                    # Test common cells
                    for col in 'ABCDEFGHIJ':
                        for row in range(1, 20):
                            cell = f'{col}{row}'
                            try:
                                if image_loader.image_in(cell):
                                    image = image_loader.get(cell)
                                    output_path = f"/home/viblio/family_films/xls2xlsx_loader_{sheet_name}_{cell}.png"
                                    image.save(output_path)
                                    print(f"    ✓ Found image in {cell}, saved to {output_path}")
                                    images_found += 1
                            except:
                                continue
                except Exception as e:
                    print(f"  Error with image loader: {e}")
            
            print(f"\nTotal images found with xls2xlsx: {images_found}")
            return images_found > 0
        else:
            print("✗ Conversion failed - no output file created")
            return False
            
    except ImportError:
        print("xls2xlsx not available")
        return False
    except Exception as e:
        print(f"Error with xls2xlsx: {e}")
        return False

def analyze_ole_structure(xls_file):
    """Analyze XLS file as OLE2 compound document"""
    print(f"\n=== OLE2 Structure Analysis ===")
    
    try:
        # XLS files are OLE2 compound documents
        # Let's try to understand the structure
        with open(xls_file, 'rb') as f:
            # Read OLE2 header
            header = f.read(512)
            
            # Check OLE2 signature
            ole_signature = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
            if header[:8] == ole_signature:
                print("✓ Valid OLE2 compound document")
                
                # Parse some basic OLE2 info
                sector_size = struct.unpack('<H', header[30:32])[0]
                num_fat_sectors = struct.unpack('<L', header[44:48])[0]
                
                print(f"  Sector size: {2**sector_size} bytes")
                print(f"  FAT sectors: {num_fat_sectors}")
                
                # Look for embedded object streams
                # This is where images would be stored in XLS files
                content = f.read()
                
                # Look for common embedded object markers
                markers = [
                    b'Pictures',
                    b'CONTENTS',
                    b'Ole10Native',
                    b'\x01\x00\x00\x02',  # OLE object header
                ]
                
                for marker in markers:
                    count = header.count(marker) + content.count(marker)
                    if count > 0:
                        print(f"  Found '{marker}' marker {count} times")
                
            else:
                print("✗ Not a valid OLE2 compound document")
                
    except Exception as e:
        print(f"Error analyzing OLE2 structure: {e}")

def test_with_actual_file():
    """Test all methods with an actual XLS file"""
    xls_file = "/home/viblio/family_films/chapter_sheets/L-55C_FROS - Bob Lindner Film 4 - Train and Lindners with Earl and Rosabell.xls"
    
    if not os.path.exists(xls_file):
        print(f"Test file not found: {xls_file}")
        return
    
    print(f"Testing with file: {os.path.basename(xls_file)}")
    print(f"File size: {os.path.getsize(xls_file):,} bytes")
    
    # Test all methods
    methods_successful = []
    
    if extract_images_from_xls_binary(xls_file):
        methods_successful.append("Binary extraction")
    
    if test_xls2xlsx_conversion(xls_file):
        methods_successful.append("xls2xlsx conversion")
    
    analyze_ole_structure(xls_file)
    
    print(f"\n=== RESULTS ===")
    if methods_successful:
        print(f"✓ Successful methods: {', '.join(methods_successful)}")
    else:
        print("✗ No methods successfully extracted images")
        print("This suggests the XLS file either:")
        print("  - Contains no embedded images")
        print("  - Uses a different image storage format")
        print("  - Has images that are not directly embedded")

if __name__ == "__main__":
    test_with_actual_file()