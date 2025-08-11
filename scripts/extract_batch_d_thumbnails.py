#!/usr/bin/env python3
"""
Extract Valid Thumbnails for Batch D Films Using import_chapter_metadata.py Technique

Uses the same extraction method as the original import_chapter_metadata.py management command
to extract valid thumbnails from Batch D chapter sheets.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter
from django.db import transaction

def get_batch_d_films():
    """Get all films that were imported as part of Batch D"""
    print("=== IDENTIFYING BATCH D FILMS ===")
    
    # Look for films that don't have YouTube thumbnails (likely Batch D)
    # and have chapters (indicating they were processed from Excel files)
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct()
    
    batch_d_candidates = []
    for film in films_with_chapters:
        # Check if film has a corresponding chapter sheet
        chapter_sheet_path = Path(f'/home/viblio/family_films/chapter_sheets/{film.file_id}*.xls')
        matching_sheets = list(Path('/home/viblio/family_films/chapter_sheets').glob(f'{film.file_id}*.xls'))
        
        if matching_sheets:
            batch_d_candidates.append((film, matching_sheets[0]))
            print(f"Found Batch D film: {film.file_id} - {film.title}")
    
    return batch_d_candidates

def extract_images_from_xls(xls_file, output_dir):
    """Extract images from .xls file using the xls_image_extractor.py script"""
    try:
        # Use the existing XLS image extractor script
        script_path = Path('/home/viblio/family_films/xls_image_extractor.py')
        
        result = subprocess.run([
            'python', str(script_path), str(xls_file), '-o', output_dir
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse the output to find extracted image paths
            extracted_files = []
            base_name = xls_file.stem
            output_path = Path(output_dir)
            
            # Look for extracted images with the expected naming pattern
            for i in range(50):  # Check up to 50 images (generous for large sheets)
                image_path = output_path / f"{base_name}_image_{i:03d}.jpg"
                if image_path.exists():
                    extracted_files.append(str(image_path))
            
            print(f"  Extracted {len(extracted_files)} images from {xls_file.name}")
            return extracted_files
        else:
            print(f"  XLS extraction failed: {result.stderr}")
            return []
    except Exception as e:
        print(f"  Error extracting images from XLS: {str(e)}")
        return []

def assign_extracted_thumbnail(chapter, image_path, thumbnail_dir="static/thumbnails/chapters"):
    """Assign an extracted image as chapter thumbnail"""
    try:
        import shutil
        
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
        
        print(f"    Assigned thumbnail: {filename}")
        return True
    except Exception as e:
        print(f"    Failed to assign thumbnail: {str(e)}")
        return False

def process_film_thumbnails(film, chapter_sheet_path):
    """Process thumbnails for a single Batch D film"""
    print(f"\n=== PROCESSING {film.file_id} ===")
    print(f"Chapter sheet: {chapter_sheet_path.name}")
    
    # Create temporary extraction directory
    extraction_dir = Path(f"/tmp/batch_d_extraction/{film.file_id}")
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract images from XLS using the same technique as import_chapter_metadata.py
    extracted_images = extract_images_from_xls(chapter_sheet_path, extraction_dir)
    
    if not extracted_images:
        print(f"  No images extracted from {chapter_sheet_path.name}")
        return 0
    
    # Get chapters for this film, ordered by their order
    chapters = list(film.chapters.all().order_by('order'))
    print(f"  Found {len(chapters)} chapters")
    
    # Assign thumbnails - using every other image starting from index 0 (Start column images)
    start_column_images = [img for i, img in enumerate(extracted_images) if i % 2 == 0]
    print(f"  Using {len(start_column_images)} Start column images")
    
    updated_count = 0
    for i, chapter in enumerate(chapters):
        if i < len(start_column_images):
            image_path = start_column_images[i]
            if assign_extracted_thumbnail(chapter, image_path):
                updated_count += 1
            print(f"    Chapter {chapter.order}: {chapter.title}")
        else:
            print(f"    Chapter {chapter.order}: No image available")
    
    return updated_count

def main():
    """Main function to extract valid thumbnails for Batch D films"""
    print("EXTRACTING VALID THUMBNAILS FOR BATCH D FILMS")
    print("Using technique from import_chapter_metadata.py management command")
    
    # Get Batch D films
    batch_d_films = get_batch_d_films()
    
    if not batch_d_films:
        print("No Batch D films found with chapter sheets")
        return 0
    
    print(f"\nFound {len(batch_d_films)} Batch D films to process")
    
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