#!/usr/bin/env python3
"""
Production-ready XLS Image Extractor

This script extracts embedded images from Excel 97-2003 (.xls) files
by parsing the binary content and locating JPEG image data.

Usage:
    python xls_image_extractor.py input.xls [output_directory]
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def extract_images_from_xls(xls_file: str, output_dir: str = None) -> List[str]:
    """
    Extract embedded JPEG images from an XLS file.
    
    Args:
        xls_file: Path to the XLS file
        output_dir: Directory to save extracted images (defaults to same directory as XLS file)
    
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
                    print(f"  ✓ Extracted image {image_count}: {width}x{height} pixels ({len(jpeg_data):,} bytes)")
                    print(f"    Saved to: {output_path}")
                    extracted_files.append(output_path)
                    image_count += 1
            except ImportError:
                # PIL not available, assume it's valid
                print(f"  ? Extracted potential image {image_count} ({len(jpeg_data):,} bytes)")
                print(f"    Saved to: {output_path} (validation skipped - PIL not available)")
                extracted_files.append(output_path)
                image_count += 1
            except Exception as e:
                # Invalid image data, remove the file
                print(f"  ✗ Invalid image data at position {start_pos}: {e}")
                os.remove(output_path)
            
            start_pos = end_pos
        
        print(f"\nExtraction complete: {len(extracted_files)} valid images extracted")
        return extracted_files
        
    except Exception as e:
        print(f"Error processing XLS file: {e}")
        return []

def batch_extract_images(xls_files: List[str], output_dir: str = None) -> dict:
    """
    Extract images from multiple XLS files.
    
    Args:
        xls_files: List of paths to XLS files
        output_dir: Directory to save all extracted images
    
    Returns:
        Dictionary mapping XLS file paths to lists of extracted image paths
    """
    results = {}
    
    for xls_file in xls_files:
        print(f"\n{'='*60}")
        print(f"Processing: {os.path.basename(xls_file)}")
        print('='*60)
        
        try:
            extracted = extract_images_from_xls(xls_file, output_dir)
            results[xls_file] = extracted
        except Exception as e:
            print(f"Error processing {xls_file}: {e}")
            results[xls_file] = []
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Extract images from Excel 97-2003 (.xls) files')
    parser.add_argument('input', help='XLS file or directory containing XLS files')
    parser.add_argument('-o', '--output', help='Output directory for extracted images')
    parser.add_argument('--batch', action='store_true', help='Process all XLS files in directory')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.input):
        # Single file processing
        if not args.input.lower().endswith('.xls'):
            print("Error: Input file must be an XLS file")
            return 1
        
        extracted = extract_images_from_xls(args.input, args.output)
        
        if extracted:
            print(f"\n✅ Success: Extracted {len(extracted)} images")
            for img_path in extracted:
                print(f"   {img_path}")
        else:
            print("\n❌ No images found or extraction failed")
        
        return 0
    
    elif os.path.isdir(args.input):
        # Directory processing
        if not args.batch:
            print("Error: Use --batch flag to process all XLS files in a directory")
            return 1
        
        # Find all XLS files in directory
        xls_files = list(Path(args.input).glob('*.xls'))
        
        if not xls_files:
            print(f"No XLS files found in {args.input}")
            return 1
        
        print(f"Found {len(xls_files)} XLS files to process")
        
        results = batch_extract_images([str(f) for f in xls_files], args.output)
        
        # Summary
        total_images = sum(len(images) for images in results.values())
        successful_files = sum(1 for images in results.values() if images)
        
        print(f"\n{'='*60}")
        print("BATCH PROCESSING SUMMARY")
        print('='*60)
        print(f"Files processed: {len(results)}")
        print(f"Files with images: {successful_files}")
        print(f"Total images extracted: {total_images}")
        
        if total_images > 0:
            print("\nFiles with extracted images:")
            for xls_file, images in results.items():
                if images:
                    print(f"  {os.path.basename(xls_file)}: {len(images)} images")
        
        return 0
    
    else:
        print(f"Error: Input path not found: {args.input}")
        return 1

if __name__ == "__main__":
    sys.exit(main())