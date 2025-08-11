#!/usr/bin/env python3
"""
Try using olefile library for better OLE compound document parsing
"""
import os
import sys
from pathlib import Path

# First try to install olefile if not available
try:
    import olefile
    print("✓ olefile available")
except ImportError:
    print("Installing olefile...")
    os.system("pip install olefile")
    import olefile

def extract_with_olefile(xls_file, output_dir):
    """Use olefile to parse the OLE compound document structure"""
    print("=== OLEFILE Method ===")
    
    try:
        # Check if it's a valid OLE file
        if not olefile.isOleFile(xls_file):
            print("✗ Not a valid OLE file")
            return
            
        print("✓ Valid OLE file detected")
        
        # Open the OLE file
        ole = olefile.OleFileIO(xls_file)
        
        # List all streams in the OLE file
        print("Streams in OLE file:")
        for stream in ole.listdir():
            print(f"  {'/'.join(stream)}")
            
        # Look for embedded objects or pictures
        for stream_path in ole.listdir():
            stream_name = '/'.join(stream_path)
            
            # Common locations for embedded objects in Excel
            if any(keyword in stream_name.lower() for keyword in ['picture', 'object', 'image', 'embed']):
                print(f"Found potential image stream: {stream_name}")
                
                try:
                    # Read the stream
                    with ole.opendir(stream_path) as stream:
                        data = stream.read()
                        
                    # Try to find image signatures in the stream
                    jpeg_start = data.find(b'\xff\xd8\xff')
                    png_start = data.find(b'\x89PNG')
                    
                    if jpeg_start != -1:
                        print(f"  Found JPEG data at offset {jpeg_start}")
                        # Extract JPEG
                        jpeg_end = data.find(b'\xff\xd9', jpeg_start)
                        if jpeg_end != -1:
                            jpeg_data = data[jpeg_start:jpeg_end + 2]
                            output_file = Path(output_dir) / f"olefile_jpeg_{stream_name.replace('/', '_')}.jpg"
                            with open(output_file, 'wb') as f:
                                f.write(jpeg_data)
                            print(f"    Saved JPEG: {output_file}")
                            
                    if png_start != -1:
                        print(f"  Found PNG data at offset {png_start}")
                        # Extract PNG
                        iend_pos = data.find(b'IEND\xae\x42\x60\x82', png_start)
                        if iend_pos != -1:
                            png_data = data[png_start:iend_pos + 8]
                            output_file = Path(output_dir) / f"olefile_png_{stream_name.replace('/', '_')}.png"
                            with open(output_file, 'wb') as f:
                                f.write(png_data)
                            print(f"    Saved PNG: {output_file}")
                            
                except Exception as e:
                    print(f"  Error reading stream {stream_name}: {e}")
        
        ole.close()
        
    except Exception as e:
        print(f"OLEFILE method failed: {e}")

def extract_excel_objects_method(xls_file, output_dir):
    """Try to locate Excel-specific object storage"""
    print("\n=== Excel Objects Method ===")
    
    try:
        ole = olefile.OleFileIO(xls_file)
        
        # Look for common Excel object storage locations
        object_streams = [
            'MBD', 'ObjectPool', '1Ole10Native', 'Ole10Native',
            'Picture', 'Pictures', 'EmbeddedObj'
        ]
        
        found_objects = []
        for stream_path in ole.listdir():
            stream_name = '/'.join(stream_path)
            
            for obj_type in object_streams:
                if obj_type.lower() in stream_name.lower():
                    found_objects.append(stream_path)
                    break
                    
        print(f"Found {len(found_objects)} potential object streams")
        
        for i, stream_path in enumerate(found_objects):
            try:
                with ole.opendir(stream_path) as stream:
                    data = stream.read()
                    
                print(f"Object {i}: {'/'.join(stream_path)} ({len(data)} bytes)")
                
                # Save raw data for analysis
                raw_file = Path(output_dir) / f"excel_object_{i:03d}.bin"
                with open(raw_file, 'wb') as f:
                    f.write(data)
                    
                # Try to find embedded images in the object data
                for fmt, sig, ext in [
                    ('JPEG', b'\xff\xd8\xff', 'jpg'),
                    ('PNG', b'\x89PNG\r\n\x1a\n', 'png'),
                    ('BMP', b'BM', 'bmp'),
                    ('GIF', b'GIF8', 'gif')
                ]:
                    sig_pos = data.find(sig)
                    if sig_pos != -1:
                        print(f"  Found {fmt} at offset {sig_pos}")
                        
                        if fmt == 'JPEG':
                            end_pos = data.find(b'\xff\xd9', sig_pos)
                            if end_pos != -1:
                                img_data = data[sig_pos:end_pos + 2]
                        elif fmt == 'PNG':
                            end_pos = data.find(b'IEND\xae\x42\x60\x82', sig_pos)
                            if end_pos != -1:
                                img_data = data[sig_pos:end_pos + 8]
                        else:
                            # For BMP/GIF, take a reasonable chunk
                            img_data = data[sig_pos:sig_pos + min(100000, len(data) - sig_pos)]
                            
                        if len(img_data) > 1000:  # Reasonable size
                            img_file = Path(output_dir) / f"excel_object_{i:03d}_{fmt.lower()}.{ext}"
                            with open(img_file, 'wb') as f:
                                f.write(img_data)
                            print(f"    Extracted {fmt}: {img_file}")
                            
            except Exception as e:
                print(f"  Error processing object {i}: {e}")
        
        ole.close()
        
    except Exception as e:
        print(f"Excel objects method failed: {e}")

def main():
    xls_file = "/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls"
    output_dir = "/tmp/olefile_test"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Testing OLE-specific extraction on: {os.path.basename(xls_file)}")
    
    extract_with_olefile(xls_file, output_dir)
    extract_excel_objects_method(xls_file, output_dir)
    
    print(f"\nFiles created in {output_dir}:")
    for f in sorted(Path(output_dir).glob("*")):
        size = f.stat().st_size
        print(f"  {f.name} ({size} bytes)")

if __name__ == "__main__":
    main()