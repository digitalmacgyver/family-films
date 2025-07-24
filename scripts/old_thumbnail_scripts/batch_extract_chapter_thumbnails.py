#!/usr/bin/env python3
"""
Batch extract chapter thumbnails from Excel files and assign them to chapters
"""
import os
import sys
import subprocess
from pathlib import Path

def extract_thumbnails_batch():
    """Extract thumbnails from all Excel files with images"""
    
    # List of Excel files known to have images (you can expand this list)
    files_with_images = [
        "57-PT_FROS - Josephine Southwest Trip Grand Canyon Bryce Canyon Zion Calico Ghost Town.xls",
        "58-V1_FROS - Road Trip Utah Nevada Wyoming Michigan.xls", 
        "58-V2_FROS - Canada Road Trip Montana Victoria BC.xls",
        "59-HI_FROS - Hawaii Trip.xls",
        "HR-1-4_FROS - Multiple Reels Mostly Haywards Myres and Wrens Victoria BC Knotts Berry Farm Tubing Christmas Rose Parade Santas Village.xls",
        "L-55C_FROS - Bob Lindner Film 4 - Train and Lindners with Earl and Rosabell.xls",
        "P-09-11_FROS - Seattle and Canada trip with Haywards and Oscar Myre and Irwin Wrens families.xls",
        "PA-02_FROS - John Jr and Joy as Babies with Myers.xls",
        "PB-04_FROS - Western Parks Rainbow Forest Grand Canyon Sequoia Yosemite Crater Lake.xls",
        "PB-05_FROS - Hume Lake Public Pool Death Valley Trip.xls"
    ]
    
    chapter_sheets_dir = Path("chapter_sheets")
    thumbnail_dir = Path("static/thumbnails/chapters")
    
    print("CHAPTER THUMBNAIL EXTRACTION")
    print("=" * 60)
    print(f"Processing {len(files_with_images)} Excel files...")
    print()
    
    success_count = 0
    error_count = 0
    
    for excel_file in files_with_images:
        file_path = chapter_sheets_dir / excel_file
        
        if not file_path.exists():
            print(f"⚠️  File not found: {excel_file}")
            error_count += 1
            continue
        
        try:
            print(f"Processing: {excel_file}")
            
            # Step 1: Extract images from Excel file
            result1 = subprocess.run([
                "python", "xls_image_extractor.py", str(file_path), "-o", str(thumbnail_dir)
            ], capture_output=True, text=True)
            
            if result1.returncode != 0:
                print(f"  ❌ Failed to extract images: {result1.stderr}")
                error_count += 1
                continue
            
            # Step 2: Run import command to assign thumbnails to chapters
            result2 = subprocess.run([
                "python", "manage.py", "import_chapter_metadata", 
                "--file", excel_file
            ], capture_output=True, text=True)
            
            if result2.returncode != 0:
                print(f"  ❌ Failed to assign thumbnails: {result2.stderr}")
                error_count += 1
                continue
            
            # Count successful assignments from output
            output_lines = result2.stdout.split('\\n')
            thumbnail_assignments = [line for line in output_lines if "Assigned thumbnail:" in line]
            
            print(f"  ✅ Successfully processed - {len(thumbnail_assignments)} thumbnails assigned")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            error_count += 1
            
        print()
    
    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total files: {len(files_with_images)}")
    
    if success_count > 0:
        print(f"\\n✨ Chapter thumbnails are now available in the development server!")
        print("   View them at http://127.0.0.1:8000/films/")
    
    return error_count == 0

if __name__ == "__main__":
    success = extract_thumbnails_batch()
    sys.exit(0 if success else 1)