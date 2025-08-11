#!/usr/bin/env python3
"""
Fix Batch D Thumbnail Extraction

Correctly extract Start column thumbnails by analyzing each XLS file
to determine if it has Start+End images (2 per row) or just Start images (1 per row).
"""

import os
import sys
import django
import subprocess
import shutil
from pathlib import Path
import pandas as pd

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter
from django.db import transaction

def analyze_xls_structure(xls_file):
    """Analyze XLS structure to determine image pattern"""
    try:
        df = pd.read_excel(xls_file, header=None)
        
        # Find header row
        header_row_idx = None
        for idx in range(min(15, len(df))):
            row = df.iloc[idx]
            row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
            if 'start' in row_str and 'title' in row_str:
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            return None
        
        # Count data rows (chapters)
        data_rows = 0
        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]
            # Look for title column (usually column 2)
            title_cell = row[2] if len(row) > 2 else None
            if pd.notna(title_cell) and str(title_cell).strip():
                data_rows += 1
        
        return {
            'header_row': header_row_idx,
            'chapter_count': data_rows
        }
        
    except Exception as e:
        print(f"Error analyzing {xls_file.name}: {e}")
        return None

def extract_images_from_xls(xls_file, output_dir):
    """Extract images from .xls file using the xls_image_extractor.py script"""
    try:
        script_path = Path('/home/viblio/family_films/xls_image_extractor.py')
        
        result = subprocess.run([
            'python', str(script_path), str(xls_file), '-o', output_dir
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Find extracted image paths
            extracted_files = []
            base_name = xls_file.stem
            output_path = Path(output_dir)
            
            for i in range(50):  # Check up to 50 images
                image_path = output_path / f"{base_name}_image_{i:03d}.jpg"
                if image_path.exists():
                    extracted_files.append(str(image_path))
            
            return extracted_files
        else:
            print(f"  XLS extraction failed: {result.stderr}")
            return []
    except Exception as e:
        print(f"  Error extracting images from XLS: {str(e)}")
        return []

def determine_start_images(extracted_images, chapter_count):
    """Determine which images are from the Start column"""
    image_count = len(extracted_images)
    
    if image_count == chapter_count:
        # 1:1 ratio - all images are Start column images
        print(f"  Pattern: 1 image per chapter (all Start column)")
        return extracted_images
    
    elif image_count == 2 * chapter_count:
        # 2:1 ratio - alternating Start/End images, take every other starting from 0
        start_images = [img for i, img in enumerate(extracted_images) if i % 2 == 0]
        print(f"  Pattern: 2 images per chapter (Start+End), using {len(start_images)} Start images")
        return start_images
    
    else:
        # Unexpected ratio - try to be smart about it
        print(f"  Warning: Unexpected image pattern ({image_count} images for {chapter_count} chapters)")
        if image_count > chapter_count:
            # Take every nth image to get chapter_count images
            step = image_count // chapter_count
            start_images = [extracted_images[i * step] for i in range(chapter_count)]
            print(f"  Using every {step}th image: {len(start_images)} images")
            return start_images
        else:
            # Fewer images than chapters - use what we have
            print(f"  Using all {image_count} available images")
            return extracted_images

def assign_extracted_thumbnail(chapter, image_path, thumbnail_dir="static/thumbnails/chapters"):
    """Assign an extracted image as chapter thumbnail"""
    try:
        # Create thumbnail directory if needed
        thumb_path = Path(thumbnail_dir)
        thumb_path.mkdir(parents=True, exist_ok=True)
        
        # Copy image to thumbnail directory with meaningful filename
        filename = f"{chapter.film.file_id}_ch{chapter.order:02d}_{chapter.start_time_seconds}s.jpg"
        dest_path = thumb_path / filename
        
        # Copy the extracted image
        shutil.copy2(image_path, dest_path)
        
        # Update chapter thumbnail URL (relative to static root)
        chapter.thumbnail_url = f"/static/thumbnails/chapters/{filename}"
        chapter.save()
        
        return True
    except Exception as e:
        print(f"    Failed to assign thumbnail: {str(e)}")
        return False

def process_film_thumbnails(film, chapter_sheet_path):
    """Process thumbnails for a single Batch D film with correct Start column logic"""
    print(f"\n=== PROCESSING {film.file_id} ===")
    
    # Analyze XLS structure
    structure = analyze_xls_structure(chapter_sheet_path)
    if not structure:
        print(f"  Could not analyze XLS structure")
        return 0
    
    # Create temporary extraction directory
    extraction_dir = Path(f"/tmp/batch_d_fix/{film.file_id}")
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract images from XLS
    extracted_images = extract_images_from_xls(chapter_sheet_path, extraction_dir)
    if not extracted_images:
        print(f"  No images extracted")
        return 0
    
    print(f"  Extracted {len(extracted_images)} total images")
    print(f"  Expected {structure['chapter_count']} chapters")
    
    # Determine which images are from Start column
    start_images = determine_start_images(extracted_images, structure['chapter_count'])
    
    # Get chapters for this film, ordered by their order
    chapters = list(film.chapters.all().order_by('order'))
    
    # Assign thumbnails
    updated_count = 0
    for i, chapter in enumerate(chapters):
        if i < len(start_images):
            image_path = start_images[i]
            if assign_extracted_thumbnail(chapter, image_path):
                updated_count += 1
                print(f"    ✓ Chapter {chapter.order}: {chapter.title}")
            else:
                print(f"    ✗ Chapter {chapter.order}: Assignment failed")
        else:
            print(f"    - Chapter {chapter.order}: No Start image available")
    
    return updated_count

def get_batch_d_films():
    """Get all films that were imported as part of Batch D"""
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct()
    
    batch_d_candidates = []
    for film in films_with_chapters:
        chapter_sheet_path = Path(f'/home/viblio/family_films/chapter_sheets/{film.file_id}*.xls')
        matching_sheets = list(Path('/home/viblio/family_films/chapter_sheets').glob(f'{film.file_id}*.xls'))
        
        if matching_sheets:
            batch_d_candidates.append((film, matching_sheets[0]))
    
    return batch_d_candidates

def main():
    """Fix Batch D thumbnail extraction"""
    print("FIXING BATCH D THUMBNAIL EXTRACTION")
    print("Correctly handling Start vs End column images")
    
    # Get Batch D films
    batch_d_films = get_batch_d_films()
    print(f"\nFound {len(batch_d_films)} Batch D films to fix")
    
    total_updated = 0
    
    # Process each film
    for film, chapter_sheet_path in batch_d_films:
        try:
            updated_count = process_film_thumbnails(film, chapter_sheet_path)
            total_updated += updated_count
        except Exception as e:
            print(f"Error processing {film.file_id}: {e}")
    
    print(f"\n✅ Successfully updated {total_updated} chapter thumbnails!")
    
    # Run collectstatic to ensure thumbnails are available
    print("\nRunning collectstatic to make thumbnails available...")
    try:
        result = subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], 
                              cwd='/home/viblio/family_films',
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ collectstatic completed successfully")
        else:
            print(f"⚠ collectstatic error: {result.stderr}")
    except Exception as e:
        print(f"⚠ Could not run collectstatic: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())