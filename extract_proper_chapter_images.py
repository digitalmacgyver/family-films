#!/usr/bin/env python3
"""
Extract proper chapter thumbnail images from .xls files using LibreOffice conversion
This replaces the corrupted binary-extracted images with the true embedded images
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import openpyxl
import hashlib
from PIL import Image

class ProperChapterImageExtractor:
    def __init__(self, chapter_sheets_dir, output_dir):
        self.chapter_sheets_dir = Path(chapter_sheets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix='chapter_extraction_'))
        
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def convert_xls_to_xlsx(self, xls_file):
        """Convert XLS to XLSX using LibreOffice (preserves images)"""
        xls_path = Path(xls_file)
        xlsx_path = self.temp_dir / f"{xls_path.stem}.xlsx"
        
        print(f"Converting {xls_path.name} to XLSX...")
        
        try:
            # Use LibreOffice to convert, preserving images
            result = subprocess.run([
                'libreoffice', 
                '--headless', 
                '--convert-to', 'xlsx', 
                '--outdir', str(self.temp_dir),
                str(xls_file)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"  ✗ LibreOffice conversion failed: {result.stderr}")
                return None
                
            if xlsx_path.exists():
                print(f"  ✓ Converted to {xlsx_path.name}")
                return xlsx_path
            else:
                print(f"  ✗ Output file not created")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ Conversion timed out")
            return None
        except Exception as e:
            print(f"  ✗ Conversion error: {e}")
            return None
    
    def extract_images_from_xlsx(self, xlsx_file, film_id):
        """Extract images from XLSX file using openpyxl"""
        try:
            wb = openpyxl.load_workbook(xlsx_file)
            images_extracted = []
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                
                # Extract images using the _images attribute
                if hasattr(sheet, '_images') and sheet._images:
                    print(f"  Found {len(sheet._images)} images in sheet: {sheet_name}")
                    
                    for i, img in enumerate(sheet._images):
                        if hasattr(img, '_data'):
                            try:
                                # Generate filename matching our current naming convention
                                # But use "proper" prefix to distinguish from corrupted versions
                                filename = f"{film_id} - {sheet_name.replace('...', '')}_proper_image_{i:03d}.jpg"
                                
                                # Clean filename of problematic characters
                                filename = filename.replace('/', '_').replace('\\', '_')
                                if len(filename) > 200:  # Filesystem limit
                                    filename = f"{film_id}_proper_image_{i:03d}.jpg"
                                
                                filepath = self.output_dir / filename
                                
                                # Write image data
                                image_data = img._data()
                                with open(filepath, 'wb') as f:
                                    f.write(image_data)
                                
                                # Validate the image
                                try:
                                    with Image.open(filepath) as pil_img:
                                        size = pil_img.size
                                        format_name = pil_img.format
                                    
                                    # Calculate checksum
                                    with open(filepath, 'rb') as f:
                                        checksum = hashlib.md5(f.read()).hexdigest()
                                    
                                    images_extracted.append({
                                        'filepath': str(filepath),
                                        'filename': filename,
                                        'size': size,
                                        'format': format_name,
                                        'checksum': checksum,
                                        'file_size': len(image_data),
                                        'index': i
                                    })
                                    
                                    print(f"    ✓ {filename} ({size[0]}x{size[1]}, {len(image_data)} bytes)")
                                    
                                except Exception as e:
                                    print(f"    ✗ Invalid image {i}: {e}")
                                    if filepath.exists():
                                        filepath.unlink()
                                        
                            except Exception as e:
                                print(f"    ✗ Error extracting image {i}: {e}")
                else:
                    print(f"  No images found in sheet: {sheet_name}")
            
            return images_extracted
            
        except Exception as e:
            print(f"  ✗ Error processing XLSX file: {e}")
            return []
    
    def process_single_file(self, xls_file):
        """Process a single XLS file"""
        xls_path = Path(xls_file)
        film_id = xls_path.stem.split(' - ')[0]  # Extract film ID from filename
        
        print(f"\n{'='*60}")
        print(f"Processing: {xls_path.name}")
        print(f"Film ID: {film_id}")
        
        # Step 1: Convert to XLSX
        xlsx_file = self.convert_xls_to_xlsx(xls_file)
        if not xlsx_file:
            return {'film_id': film_id, 'status': 'conversion_failed', 'images': []}
        
        # Step 2: Extract images
        images = self.extract_images_from_xlsx(xlsx_file, film_id)
        
        result = {
            'film_id': film_id,
            'original_file': str(xls_file),
            'images_extracted': len(images),
            'images': images,
            'status': 'success' if images else 'no_images'
        }
        
        print(f"Result: {result['status']} - {len(images)} images extracted")
        return result
    
    def process_all_files(self):
        """Process all XLS files in the chapter sheets directory"""
        xls_files = list(self.chapter_sheets_dir.glob('*.xls'))
        
        if not xls_files:
            print(f"No .xls files found in {self.chapter_sheets_dir}")
            return []
        
        print(f"Found {len(xls_files)} XLS files to process")
        
        results = []
        total_images = 0
        
        for xls_file in sorted(xls_files):
            try:
                result = self.process_single_file(xls_file)
                results.append(result)
                total_images += result['images_extracted']
            except KeyboardInterrupt:
                print("\n⚠️  Processing interrupted by user")
                break
            except Exception as e:
                print(f"✗ Fatal error processing {xls_file.name}: {e}")
                results.append({
                    'film_id': xls_file.stem.split(' - ')[0],
                    'original_file': str(xls_file),
                    'status': 'fatal_error',
                    'error': str(e),
                    'images': []
                })
        
        # Summary
        print(f"\n{'='*60}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Files processed: {len(results)}")
        print(f"Total images extracted: {total_images}")
        print(f"Files with images: {sum(1 for r in results if r['images_extracted'] > 0)}")
        print(f"Failed conversions: {sum(1 for r in results if r['status'] == 'conversion_failed')}")
        
        return results
    
    def generate_comparison_report(self, results):
        """Generate a report comparing old vs new images"""
        report_file = self.output_dir / "proper_extraction_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("PROPER CHAPTER IMAGE EXTRACTION REPORT\n")
            f.write("=====================================\n\n")
            f.write(f"Extraction date: {subprocess.check_output(['date']).decode().strip()}\n")
            f.write(f"Total files processed: {len(results)}\n")
            f.write(f"Method: LibreOffice conversion + openpyxl extraction\n\n")
            
            for result in results:
                f.write(f"Film: {result['film_id']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Images extracted: {result['images_extracted']}\n")
                
                if result['images']:
                    f.write("Images:\n")
                    for img in result['images']:
                        f.write(f"  - {img['filename']}\n")
                        f.write(f"    Size: {img['size']}\n")
                        f.write(f"    Checksum: {img['checksum']}\n")
                f.write("\n")
        
        print(f"Report saved to: {report_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_proper_chapter_images.py <chapter_sheets_dir> [output_dir]")
        print("  python extract_proper_chapter_images.py --test-single <xls_file>")
        return 1
    
    if sys.argv[1] == '--test-single':
        if len(sys.argv) < 3:
            print("Usage: python extract_proper_chapter_images.py --test-single <xls_file>")
            return 1
        
        # Test with single file
        extractor = ProperChapterImageExtractor(
            chapter_sheets_dir=Path(sys.argv[2]).parent,
            output_dir=Path('./proper_chapter_thumbnails')
        )
        
        try:
            result = extractor.process_single_file(sys.argv[2])
            print(f"\nTest result: {result}")
            return 0
        finally:
            extractor.cleanup()
    
    else:
        # Process all files
        chapter_sheets_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else './proper_chapter_thumbnails'
        
        extractor = ProperChapterImageExtractor(chapter_sheets_dir, output_dir)
        
        try:
            print("PROPER CHAPTER IMAGE EXTRACTION")
            print("=" * 60)
            print(f"Input directory: {chapter_sheets_dir}")
            print(f"Output directory: {output_dir}")
            print("Method: LibreOffice conversion + openpyxl extraction")
            print("This will replace corrupted binary-extracted images\n")
            
            results = extractor.process_all_files()
            extractor.generate_comparison_report(results)
            
            return 0
            
        finally:
            extractor.cleanup()

if __name__ == '__main__':
    sys.exit(main())