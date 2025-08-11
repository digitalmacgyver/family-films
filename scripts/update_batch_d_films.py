#!/usr/bin/env python3
"""
Update Batch D Films

Updates Batch D films with proper YouTube IDs and thumbnail URLs
"""

import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

class BatchDFilmUpdater:
    def __init__(self):
        self.mapping_file = '/home/viblio/family_films/scripts/batch_d_video_mapping.json'
        self.mappings = []
        self.stats = {
            'films_updated': 0,
            'youtube_ids_updated': 0,
            'thumbnails_updated': 0,
            'errors': 0,
            'not_found': 0
        }

    def load_mappings(self):
        """Load video mappings"""
        try:
            with open(self.mapping_file, 'r') as f:
                self.mappings = json.load(f)
                print(f"✅ Loaded {len(self.mappings)} video mappings")
        except Exception as e:
            print(f"❌ Could not load mappings: {e}")
            return False
        return True

    def update_film_records(self):
        """Update film records with YouTube IDs and thumbnail URLs"""
        print(f"🚀 Updating {len(self.mappings)} film records...\n")
        
        for i, mapping in enumerate(self.mappings, 1):
            file_id = mapping['file_id']
            youtube_id = mapping['youtube_id']
            title = mapping['title']
            
            print(f"[{i:2d}/{len(self.mappings)}] Processing: {file_id}")
            print(f"    📺 YouTube: {youtube_id}")
            print(f"    🎬 Title: {title[:60]}...")
            
            try:
                film = Film.objects.get(file_id=file_id)
                
                # Track what we're updating
                changes = []
                
                # Update YouTube ID if it's currently a placeholder
                if film.youtube_id.startswith('placeholder_'):
                    old_youtube_id = film.youtube_id
                    film.youtube_id = youtube_id
                    film.youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
                    changes.append(f"YouTube ID: {old_youtube_id} → {youtube_id}")
                    self.stats['youtube_ids_updated'] += 1
                
                # Update thumbnail URL to use YouTube thumbnail
                thumbnail_filename = f"{file_id}.jpg"
                thumbnail_path = f"main/thumbnails/{thumbnail_filename}"
                
                # Check if we downloaded a real thumbnail for this video
                actual_thumbnail_path = f"/home/viblio/family_films/main/static/{thumbnail_path}"
                if os.path.exists(actual_thumbnail_path):
                    new_thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg"
                    old_thumbnail_url = film.thumbnail_url
                    film.thumbnail_url = new_thumbnail_url
                    changes.append(f"Thumbnail: {old_thumbnail_url} → {new_thumbnail_url}")
                    self.stats['thumbnails_updated'] += 1
                
                if changes:
                    film.save()
                    self.stats['films_updated'] += 1
                    print(f"    ✅ Updated:")
                    for change in changes:
                        print(f"       {change}")
                else:
                    print(f"    ⏩ No changes needed")
                
            except Film.DoesNotExist:
                print(f"    ⚠️ Film not found: {file_id}")
                self.stats['not_found'] += 1
            except Exception as e:
                print(f"    ❌ Error updating film {file_id}: {e}")
                self.stats['errors'] += 1
            
            print()  # Empty line for readability

    def print_summary(self):
        """Print processing summary"""
        print("=" * 60)
        print("BATCH D FILM UPDATE SUMMARY")
        print("=" * 60)
        print(f"Mappings processed: {len(self.mappings)}")
        print(f"Films updated: {self.stats['films_updated']}")
        print(f"YouTube IDs updated: {self.stats['youtube_ids_updated']}")
        print(f"Thumbnails updated: {self.stats['thumbnails_updated']}")
        print(f"Films not found: {self.stats['not_found']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    print("=== BATCH D FILM UPDATER ===\n")
    
    updater = BatchDFilmUpdater()
    
    if not updater.load_mappings():
        return 1
    
    updater.update_film_records()
    updater.print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())