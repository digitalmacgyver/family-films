#!/usr/bin/env python3
"""
Try to extract raw bitmap or other image formats from Excel
"""
import os
import struct
from pathlib import Path
from PIL import Image

def search_for_raw_bitmaps(xls_file, output_dir):
    """Search for raw bitmap data or other image representations"""
    print("=== Raw Bitmap Search ===")
    
    try:
        with open(xls_file, 'rb') as f:
            data = f.read()
            
        print(f"Searching {len(data)} bytes for bitmap patterns...")
        
        # Look for Windows DIB (Device Independent Bitmap) headers
        # DIB header starts with size field (40 bytes = 0x28000000 in little endian)
        dib_signature = struct.pack('<I', 40)  # DIB header size
        
        pos = 0
        bitmap_count = 0
        
        while True:
            pos = data.find(dib_signature, pos)
            if pos == -1:
                break
                
            try:
                # Parse potential DIB header
                if pos + 40 < len(data):
                    header = struct.unpack('<IIIHHIIIIII', data[pos:pos+40])
                    header_size, width, height, planes, bits_per_pixel, compression, image_size = header[:7]
                    
                    print(f"Potential DIB at offset {pos:08X}:")
                    print(f"  Size: {width}x{height}, {bits_per_pixel} bpp, compression: {compression}")
                    
                    # Check if dimensions are reasonable (for thumbnails)
                    if 50 <= width <= 800 and 50 <= height <= 600 and bits_per_pixel in [8, 24, 32]:
                        # Calculate expected image data size
                        row_size = ((width * bits_per_pixel + 31) // 32) * 4  # 4-byte aligned
                        expected_size = row_size * abs(height)
                        
                        print(f"  Expected data size: {expected_size} bytes")
                        
                        # Look for the actual bitmap data (might be right after header)
                        bitmap_start = pos + 40
                        if bitmap_start + expected_size <= len(data):
                            bitmap_data = data[bitmap_start:bitmap_start + expected_size]
                            
                            try:
                                # Create a proper BMP file with file header
                                file_header = struct.pack('<HLHHL', 
                                    0x4D42,  # 'BM' signature
                                    14 + 40 + expected_size,  # File size
                                    0, 0,  # Reserved
                                    14 + 40  # Offset to image data
                                )
                                
                                bmp_file = Path(output_dir) / f"raw_bitmap_{bitmap_count:03d}_{pos:08X}.bmp"
                                with open(bmp_file, 'wb') as f:
                                    f.write(file_header)
                                    f.write(data[pos:pos+40])  # DIB header
                                    f.write(bitmap_data)
                                
                                # Try to validate with PIL
                                with Image.open(bmp_file) as img:
                                    img_width, img_height = img.size
                                    print(f"  ✓ Valid BMP created: {img_width}x{img_height}")
                                    bitmap_count += 1
                                    
                            except Exception as e:
                                print(f"  ✗ Failed to create valid BMP: {e}")
                                if bmp_file.exists():
                                    os.remove(bmp_file)
                    
            except struct.error as e:
                print(f"  ✗ Struct error at {pos:08X}: {e}")
            
            pos += 4
        
        print(f"Found {bitmap_count} raw bitmaps")
        
    except Exception as e:
        print(f"Raw bitmap search failed: {e}")

def search_for_wmf_emf(xls_file, output_dir):
    """Search for Windows Metafiles (WMF/EMF) which Excel sometimes uses"""
    print("\n=== WMF/EMF Search ===")
    
    try:
        with open(xls_file, 'rb') as f:
            data = f.read()
            
        # WMF signature: D7 CD C6 9A (placeable metafile header)
        # EMF signature: 01 00 00 00 (at start of EMF header)
        
        signatures = [
            ('WMF', b'\xd7\xcd\xc6\x9a', 'wmf'),
            ('EMF', b'\x01\x00\x00\x00', 'emf'),  # This is very generic, will need more validation
        ]
        
        for sig_name, sig_bytes, ext in signatures:
            pos = 0
            count = 0
            
            while True:
                pos = data.find(sig_bytes, pos)
                if pos == -1:
                    break
                    
                # For EMF, need additional validation as signature is generic
                if sig_name == 'EMF' and pos + 80 < len(data):
                    # Check if this looks like an EMF header
                    try:
                        # EMF header has specific structure
                        emf_header = struct.unpack('<IIIIIIIIIIII', data[pos:pos+48])
                        record_type, record_size = emf_header[0], emf_header[1]
                        if record_type != 1 or record_size < 80:  # EMF_HEADER record
                            pos += 4
                            continue
                    except:
                        pos += 4
                        continue
                
                # Extract a reasonable chunk
                chunk_size = min(100000, len(data) - pos)
                metafile_data = data[pos:pos + chunk_size]
                
                metafile = Path(output_dir) / f"{sig_name.lower()}_{count:03d}_{pos:08X}.{ext}"
                with open(metafile, 'wb') as f:
                    f.write(metafile_data)
                
                print(f"Found {sig_name} at offset {pos:08X}, size {len(metafile_data)}")
                count += 1
                
                pos += len(sig_bytes)
        
    except Exception as e:
        print(f"WMF/EMF search failed: {e}")

def search_for_ole_objects(xls_file, output_dir):
    """Look for OLE embedded objects that might contain images"""
    print("\n=== OLE Object Search ===")
    
    try:
        with open(xls_file, 'rb') as f:
            data = f.read()
            
        # Look for OLE object signatures
        ole_signatures = [
            b'Paint.Picture',  # Paint brush objects
            b'Paintbrush Picture',
            b'Package',  # Packaged objects
            b'PBrush',   # Paint brush
            b'MSPhotoEd.3',  # Photo editor
            b'Bitmap Image',
            b'Picture (Device Independent Bitmap)'
        ]
        
        found_objects = 0
        
        for sig in ole_signatures:
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1:
                    break
                    
                print(f"Found OLE object signature '{sig.decode('ascii', errors='ignore')}' at offset {pos:08X}")
                
                # Extract surrounding data
                start_pos = max(0, pos - 1000)
                end_pos = min(len(data), pos + 50000)
                obj_data = data[start_pos:end_pos]
                
                obj_file = Path(output_dir) / f"ole_object_{found_objects:03d}_{pos:08X}.bin"
                with open(obj_file, 'wb') as f:
                    f.write(obj_data)
                
                print(f"  Extracted to: {obj_file} ({len(obj_data)} bytes)")
                found_objects += 1
                
                pos += len(sig)
        
        print(f"Found {found_objects} OLE objects")
        
    except Exception as e:
        print(f"OLE object search failed: {e}")

def main():
    xls_file = "/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls"
    output_dir = "/tmp/raw_extraction"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Raw format search in: {os.path.basename(xls_file)}")
    
    search_for_raw_bitmaps(xls_file, output_dir)
    search_for_wmf_emf(xls_file, output_dir)
    search_for_ole_objects(xls_file, output_dir)
    
    print(f"\nAll extracted files:")
    for f in sorted(Path(output_dir).glob("*")):
        size = f.stat().st_size
        print(f"  {f.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()