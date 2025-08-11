#!/usr/bin/env python3
"""
Fix Chapter Thumbnails

Re-processes chapter thumbnails for existing chapters using the correct extracted images.
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

class ChapterThumbnailFixer:
    def __init__(self):
        self.chapter_sheets_dir = Path('/home/viblio/family_films/chapter_sheets')
        self.thumbnail_dir = Path('/home/viblio/family_films/main/static/thumbnails/chapters')
        self.stats = {
            'chapters_updated': 0,
            'images_assigned': 0,
            'errors': 0
        }

    def get_batch_d_film_ids(self):
        """Get list of Batch D film IDs that have chapters"""
        batch_d_patterns = [
            "75-SLD_FROS", "76A-SLD_FROS", "76B-SLD_FROS", "76C-SLD_FROS", 
            "76D-SLD_FROS", "76E-SLD_FROS", "77-SLD_FROS", "RLD-R01_FROS", 
            "RLD-R02_FROS", "SLD-01_FROS", "SLD-02_FROS", "SLD-03_FROS", 
            "SLD-04_FROS", "SLD-05_FROS", "SLD-06_FROS", "SLD-07_FROS", 
            "SLD-08_FROS", "SLD-09_FROS", "SLD-10_FROS", "SLD-11_FROS", 
            "SLD-12_FROS", "SLD-13_FROS", "SLD-14_FROS", "SLD-15_FROS", 
            "SLD-16_FROS", "SLD-17_FROS", "SLD-18_FROS", "SLD-19_FROS", 
            "SLD-20_FROS", "SLD-21_FROS", "SLD-R01_FROS", 
            "SLD-R03_FROS", "SLD-R04_FROS"
        ]
        
        film_ids = []
        for pattern in batch_d_patterns:
            try:
                film = Film.objects.get(file_id=pattern)
                if film.chapters.exists():
                    film_ids.append(pattern)
            except Film.DoesNotExist:
                continue
        
        return film_ids

    def get_extracted_images_for_film(self, film_id):
        """Get list of extracted images for a film"""
        film_image_dir = self.thumbnail_dir / film_id
        if not film_image_dir.exists():
            return []
        
        # Find all extracted images, sorted by filename
        image_files = []
        for i in range(50):  # Check up to 50 images
            image_file = film_image_dir / f"*_image_{i:03d}.jpg"
            matching_files = list(film_image_dir.glob(f"*_image_{i:03d}.jpg"))
            if matching_files:
                image_files.append(matching_files[0])
            else:
                break
        
        return sorted(image_files)

    def assign_chapter_thumbnail(self, chapter, image_path):
        """Assign extracted image as chapter thumbnail using the original image"""
        try:
            # Use the original extracted image filename (relative to static directory)
            relative_path = str(image_path).replace('/home/viblio/family_films/main/static', '')
            
            # Update chapter with thumbnail URL
            chapter.thumbnail_url = relative_path
            chapter.save()
            
            print(f"      📷 Thumbnail: {image_path.name}")
            self.stats['images_assigned'] += 1
            return True
            
        except Exception as e:
            print(f"      ❌ Error assigning thumbnail: {e}")
            self.stats['errors'] += 1
            return False

    def fix_film_thumbnails(self, film_id):
        """Fix thumbnails for all chapters in a film"""
        print(f"\n📁 Processing: {film_id}")
        
        try:
            film = Film.objects.get(file_id=film_id)
            chapters = film.chapters.all().order_by('order')
            extracted_images = self.get_extracted_images_for_film(film_id)
            
            print(f"    🎬 Film: {film_id} - {film.title}")
            print(f"    📝 Chapters: {chapters.count()}")
            print(f"    📷 Extracted images: {len(extracted_images)}")
            
            if not extracted_images:
                print(f"    ⚠️ No extracted images found")
                return
            
            chapters_updated = 0
            for i, chapter in enumerate(chapters):
                if i < len(extracted_images):
                    # Assign the corresponding extracted image
                    old_thumbnail = chapter.thumbnail_url
                    if self.assign_chapter_thumbnail(chapter, extracted_images[i]):
                        print(f"        Updated: {chapter.title}")
                        print(f"        Old: {old_thumbnail}")
                        print(f"        New: {chapter.thumbnail_url}")
                        chapters_updated += 1
                else:
                    print(f"      ⚠️ No image available for chapter {i+1}: {chapter.title}")
            
            print(f"    ✅ Updated {chapters_updated} chapter thumbnails")
            self.stats['chapters_updated'] += chapters_updated
            
        except Film.DoesNotExist:
            print(f"    ❌ Film not found: {film_id}")
            self.stats['errors'] += 1
        except Exception as e:
            print(f"    ❌ Error processing film: {e}")
            self.stats['errors'] += 1

    def fix_all_thumbnails(self):
        """Fix thumbnails for all Batch D films"""
        print("=== CHAPTER THUMBNAIL FIXER ===\n")
        
        film_ids = self.get_batch_d_film_ids()
        print(f"Found {len(film_ids)} Batch D films with chapters\n")
        
        for film_id in film_ids:
            self.fix_film_thumbnails(film_id)
        
        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("CHAPTER THUMBNAIL FIX SUMMARY")
        print("=" * 60)
        print(f"Films processed: {len(self.get_batch_d_film_ids())}")
        print(f"Chapters updated: {self.stats['chapters_updated']}")
        print(f"Images assigned: {self.stats['images_assigned']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    fixer = ChapterThumbnailFixer()
    fixer.fix_all_thumbnails()
    return 0

if __name__ == "__main__":
    sys.exit(main())