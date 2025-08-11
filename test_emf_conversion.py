#!/usr/bin/env python3
"""
Try to convert EMF files to readable image formats
"""
import os
import subprocess
from pathlib import Path

def try_imagemagick_conversion():
    """Try converting EMF files using ImageMagick"""
    print("=== ImageMagick EMF Conversion ===")
    
    emf_dir = Path("/tmp/raw_extraction")
    output_dir = Path("/tmp/emf_converted")
    output_dir.mkdir(exist_ok=True)
    
    # Try a few representative EMF files of different sizes
    test_files = [
        "emf_058_00005AAB.emf",  # Medium size
        "emf_059_00008D34.emf",  # Different size  
        "emf_060_0000B45F.emf",  # Another size
    ]
    
    for emf_file in test_files:
        emf_path = emf_dir / emf_file
        if not emf_path.exists():
            continue
            
        # Try converting to PNG
        png_output = output_dir / f"{emf_file.replace('.emf', '.png')}"
        
        try:
            result = subprocess.run([
                'convert', str(emf_path), str(png_output)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and png_output.exists():
                size = png_output.stat().st_size
                print(f"✓ Converted {emf_file} -> {png_output.name} ({size} bytes)")
                
                # Try to get image dimensions
                try:
                    identify_result = subprocess.run([
                        'identify', str(png_output)
                    ], capture_output=True, text=True, timeout=10)
                    
                    if identify_result.returncode == 0:
                        print(f"  Info: {identify_result.stdout.strip()}")
                        
                except Exception as e:
                    print(f"  Could not identify: {e}")
                    
            else:
                print(f"✗ Failed to convert {emf_file}")
                if result.stderr:
                    print(f"  Error: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout converting {emf_file}")
        except FileNotFoundError:
            print("✗ ImageMagick not found - install with: sudo apt-get install imagemagick")
            break
        except Exception as e:
            print(f"✗ Error converting {emf_file}: {e}")

def try_emf_to_bitmap_extraction():
    """Try to extract embedded bitmaps from EMF files"""
    print("\n=== EMF Bitmap Extraction ===")
    
    emf_dir = Path("/tmp/raw_extraction")
    output_dir = Path("/tmp/emf_bitmaps")
    output_dir.mkdir(exist_ok=True)
    
    # Look for EMF files that might contain bitmaps
    large_emfs = [f for f in emf_dir.glob("*.emf") if f.stat().st_size > 10000]
    
    print(f"Analyzing {len(large_emfs)} large EMF files for embedded bitmaps...")
    
    bitmap_count = 0
    
    for emf_file in large_emfs[:5]:  # Test first 5
        print(f"\nAnalyzing: {emf_file.name}")
        
        try:
            with open(emf_file, 'rb') as f:
                data = f.read()
                
            # Look for DIB (Device Independent Bitmap) data in EMF
            # EMF records that can contain bitmaps:
            # - EMR_BITBLT (0x4C)
            # - EMR_STRETCHBLT (0x4D) 
            # - EMR_STRETCHDIBITS (0x51)
            
            # Search for bitmap signatures within EMF data
            signatures = [
                ('DIB', b'\x28\x00\x00\x00'),  # DIB header size = 40
                ('JPEG', b'\xff\xd8\xff'),
                ('PNG', b'\x89PNG'),
            ]
            
            for sig_name, sig_bytes, in signatures:
                pos = 0
                while True:
                    pos = data.find(sig_bytes, pos)
                    if pos == -1:
                        break
                        
                    print(f"  Found {sig_name} signature at offset {pos:08X}")
                    
                    if sig_name == 'DIB':
                        # Try to extract DIB data
                        if pos + 40 < len(data):
                            try:
                                import struct
                                header = struct.unpack('<IIIHHII', data[pos:pos+28])
                                width, height, planes, bpp, compression = header[1:6]
                                
                                if 10 <= width <= 1000 and 10 <= height <= 1000 and bpp in [8, 24, 32]:
                                    print(f"    DIB: {width}x{height}, {bpp}bpp")
                                    
                                    # Calculate bitmap size
                                    row_size = ((width * bpp + 31) // 32) * 4
                                    bitmap_size = row_size * abs(height)
                                    
                                    if pos + 40 + bitmap_size < len(data):
                                        # Create complete BMP file
                                        file_header = struct.pack('<HLHHL', 
                                            0x4D42,  # 'BM'
                                            14 + 40 + bitmap_size,  # File size
                                            0, 0,  # Reserved
                                            14 + 40  # Offset to bitmap data
                                        )
                                        
                                        bmp_file = output_dir / f"emf_bitmap_{bitmap_count:03d}_{emf_file.stem}.bmp"
                                        with open(bmp_file, 'wb') as bf:
                                            bf.write(file_header)
                                            bf.write(data[pos:pos + 40 + bitmap_size])
                                        
                                        print(f"    Extracted DIB to: {bmp_file.name}")
                                        bitmap_count += 1
                                        
                            except Exception as e:
                                print(f"    Error processing DIB: {e}")
                    
                    elif sig_name in ['JPEG', 'PNG']:
                        # Extract embedded JPEG/PNG
                        end_sigs = {'JPEG': b'\xff\xd9', 'PNG': b'IEND\xae\x42\x60\x82'}
                        end_sig = end_sigs[sig_name]
                        
                        end_pos = data.find(end_sig, pos)
                        if end_pos != -1:
                            if sig_name == 'JPEG':
                                img_data = data[pos:end_pos + 2]
                            else:
                                img_data = data[pos:end_pos + 8]
                            
                            if len(img_data) > 1000:
                                ext = 'jpg' if sig_name == 'JPEG' else 'png'
                                img_file = output_dir / f"emf_{sig_name.lower()}_{bitmap_count:03d}_{emf_file.stem}.{ext}"
                                
                                with open(img_file, 'wb') as imgf:
                                    imgf.write(img_data)
                                
                                print(f"    Extracted {sig_name} to: {img_file.name}")
                                bitmap_count += 1
                    
                    pos += len(sig_bytes)
                    
        except Exception as e:
            print(f"  Error analyzing {emf_file.name}: {e}")
    
    print(f"\nTotal bitmaps extracted: {bitmap_count}")

def main():
    print("Testing EMF file conversion and bitmap extraction...")
    
    try_imagemagick_conversion()
    try_emf_to_bitmap_extraction()
    
    # List all output files
    for output_dir in ["/tmp/emf_converted", "/tmp/emf_bitmaps"]:
        if Path(output_dir).exists():
            print(f"\nFiles in {output_dir}:")
            for f in sorted(Path(output_dir).glob("*")):
                size = f.stat().st_size
                print(f"  {f.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()