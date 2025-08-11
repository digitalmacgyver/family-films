#!/usr/bin/env python3
"""
Deep analysis of Excel Workbook stream to find embedded images
"""
import os
import olefile
from pathlib import Path

def analyze_workbook_stream(xls_file, output_dir):
    """Analyze the Workbook stream in detail"""
    print("=== Deep Workbook Stream Analysis ===")
    
    try:
        ole = olefile.OleFileIO(xls_file)
        
        # Read the entire Workbook stream
        workbook_data = ole.opendir(['Workbook']).read()
        print(f"Workbook stream size: {len(workbook_data)} bytes")
        
        # Look for BIFF records that might contain image data
        # BIFF record structure: [record_type:2 bytes][length:2 bytes][data:length bytes]
        
        pos = 0
        record_count = 0
        image_records = []
        
        while pos < len(workbook_data) - 4:
            # Read record header
            record_type = int.from_bytes(workbook_data[pos:pos+2], 'little')
            record_length = int.from_bytes(workbook_data[pos+2:pos+4], 'little')
            
            if record_length > len(workbook_data) - pos - 4:
                break
                
            record_data = workbook_data[pos+4:pos+4+record_length]
            
            # Look for records that might contain images
            # Common BIFF record types for embedded objects:
            # 0x005D = OBJ (Object)
            # 0x00E5 = IMDATA (Image Data) 
            # 0x007F = IMGDATA
            # 0x00A9 = COORDLIST
            # 0x00AA = GCBPROC
            
            if record_type in [0x005D, 0x00E5, 0x007F, 0x00A9, 0x00AA]:
                print(f"Found potential image record: type=0x{record_type:04X}, length={record_length}")
                image_records.append((record_type, pos, record_data))
                
                # Save the record data
                record_file = Path(output_dir) / f"biff_record_{record_type:04X}_{pos:08X}.bin"
                with open(record_file, 'wb') as f:
                    f.write(record_data)
            
            # Look for embedded JPEG/PNG data within any record
            if record_length > 100:  # Only check substantial records
                # JPEG signatures
                for jpeg_sig in [b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb']:
                    jpg_pos = record_data.find(jpeg_sig)
                    if jpg_pos != -1:
                        print(f"  JPEG signature found in record 0x{record_type:04X} at offset {jpg_pos}")
                        # Extract potential JPEG
                        jpg_end = record_data.find(b'\xff\xd9', jpg_pos)
                        if jpg_end != -1:
                            jpg_data = record_data[jpg_pos:jpg_end+2]
                            if len(jpg_data) > 1000:
                                jpg_file = Path(output_dir) / f"workbook_jpeg_{record_type:04X}_{pos:08X}.jpg"
                                with open(jpg_file, 'wb') as f:
                                    f.write(jpg_data)
                                print(f"    Extracted JPEG: {jpg_file}")
                
                # PNG signature
                png_pos = record_data.find(b'\x89PNG\r\n\x1a\n')
                if png_pos != -1:
                    print(f"  PNG signature found in record 0x{record_type:04X} at offset {png_pos}")
                    png_end = record_data.find(b'IEND\xae\x42\x60\x82', png_pos)
                    if png_end != -1:
                        png_data = record_data[png_pos:png_end+8]
                        png_file = Path(output_dir) / f"workbook_png_{record_type:04X}_{pos:08X}.png"
                        with open(png_file, 'wb') as f:
                            f.write(png_data)
                        print(f"    Extracted PNG: {png_file}")
            
            pos += 4 + record_length
            record_count += 1
        
        print(f"Processed {record_count} BIFF records")
        print(f"Found {len(image_records)} potential image-related records")
        
        ole.close()
        
    except Exception as e:
        print(f"Workbook analysis failed: {e}")

def brute_force_image_search(xls_file, output_dir):
    """Brute force search for any image signatures in the entire file"""
    print("\n=== Brute Force Image Search ===")
    
    try:
        with open(xls_file, 'rb') as f:
            data = f.read()
            
        print(f"File size: {len(data)} bytes")
        
        # Search for all possible image format signatures
        signatures = [
            ('JPEG_E0', b'\xff\xd8\xff\xe0', b'\xff\xd9', 'jpg'),
            ('JPEG_E1', b'\xff\xd8\xff\xe1', b'\xff\xd9', 'jpg'), 
            ('JPEG_DB', b'\xff\xd8\xff\xdb', b'\xff\xd9', 'jpg'),
            ('JPEG_C0', b'\xff\xd8\xff\xc0', b'\xff\xd9', 'jpg'),
            ('PNG', b'\x89PNG\r\n\x1a\n', b'IEND\xae\x42\x60\x82', 'png'),
            ('BMP', b'BM', None, 'bmp'),
            ('GIF87', b'GIF87a', b'\x00\x3b', 'gif'),
            ('GIF89', b'GIF89a', b'\x00\x3b', 'gif'),
        ]
        
        found_images = 0
        
        for sig_name, start_sig, end_sig, ext in signatures:
            pos = 0
            sig_count = 0
            
            while True:
                pos = data.find(start_sig, pos)
                if pos == -1:
                    break
                    
                if end_sig:
                    end_pos = data.find(end_sig, pos + len(start_sig))
                    if end_pos != -1:
                        if sig_name.startswith('JPEG'):
                            img_data = data[pos:end_pos + 2]
                        else:
                            img_data = data[pos:end_pos + len(end_sig)]
                    else:
                        # No end marker found, skip
                        pos += len(start_sig)
                        continue
                else:
                    # For formats without clear end markers, take a chunk
                    img_data = data[pos:pos + min(50000, len(data) - pos)]
                
                if len(img_data) > 500:  # Minimum reasonable size
                    img_file = Path(output_dir) / f"bruteforce_{sig_name}_{sig_count:03d}_offset{pos:08X}.{ext}"
                    with open(img_file, 'wb') as f:
                        f.write(img_data)
                    
                    print(f"Found {sig_name}: offset {pos:08X}, size {len(img_data)}")
                    
                    # Try to validate with PIL if it's a known format
                    if ext in ['jpg', 'png', 'gif', 'bmp']:
                        try:
                            from PIL import Image
                            with Image.open(img_file) as img:
                                w, h = img.size
                                print(f"  ✓ Valid {ext.upper()}: {w}x{h}")
                                found_images += 1
                        except Exception as e:
                            print(f"  ✗ Invalid {ext.upper()}: {e}")
                            os.remove(img_file)  # Remove invalid files
                    else:
                        found_images += 1
                    
                    sig_count += 1
                
                pos += len(start_sig)
        
        print(f"\nTotal valid images found: {found_images}")
        
    except Exception as e:
        print(f"Brute force search failed: {e}")

def main():
    xls_file = "/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls"
    output_dir = "/tmp/deep_analysis"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Deep analysis of: {os.path.basename(xls_file)}")
    
    analyze_workbook_stream(xls_file, output_dir)
    brute_force_image_search(xls_file, output_dir)
    
    print(f"\nAll files created in {output_dir}:")
    for f in sorted(Path(output_dir).glob("*")):
        size = f.stat().st_size
        print(f"  {f.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()