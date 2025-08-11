#!/usr/bin/env python3
"""
Remove Films Script

Removes specified films from the database and deletes their associated thumbnail files.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

class FilmRemover:
    def __init__(self):
        self.films_to_remove = [
            "ADS_FROS",
            "ADS_FROS-SAFE", 
            "CART_FROS",
            "CART_FROS-SAFE"
        ]
        self.stats = {
            'films_removed': 0,
            'thumbnails_deleted': 0,
            'films_not_found': 0,
            'errors': 0
        }

    def find_and_delete_thumbnails(self, file_id):
        """Find and delete all thumbnail files for a film"""
        thumbnail_dirs = [
            Path('/home/viblio/family_films/main/static/main/thumbnails'),
            Path('/home/viblio/family_films/main/static/thumbnails/films')
        ]
        
        deleted_files = []
        
        for thumbnail_dir in thumbnail_dirs:
            if thumbnail_dir.exists():
                # Look for various thumbnail file patterns
                patterns = [
                    f"{file_id}.jpg",
                    f"{file_id}.jpeg", 
                    f"{file_id}.png",
                    f"{file_id}_default.jpg",
                    f"{file_id}_maxres.jpg",
                    f"{file_id}_medium.jpg",
                    f"{file_id}_high.jpg"
                ]
                
                for pattern in patterns:
                    thumbnail_file = thumbnail_dir / pattern
                    if thumbnail_file.exists():
                        try:
                            thumbnail_file.unlink()
                            deleted_files.append(str(thumbnail_file))
                            self.stats['thumbnails_deleted'] += 1
                        except Exception as e:
                            print(f"    ⚠️ Could not delete {thumbnail_file}: {e}")
        
        return deleted_files

    def remove_films(self):
        """Remove films and their thumbnails"""
        print(f"🗑️ Removing {len(self.films_to_remove)} films from database...\n")
        
        for i, file_id in enumerate(self.films_to_remove, 1):
            print(f"[{i}/{len(self.films_to_remove)}] Processing: {file_id}")
            
            try:
                # Find the film
                film = Film.objects.get(file_id=file_id)
                
                print(f"    📽️ Found film: {film.title}")
                print(f"    🔗 YouTube ID: {film.youtube_id}")
                
                # Delete thumbnail files first
                deleted_thumbnails = self.find_and_delete_thumbnails(file_id)
                if deleted_thumbnails:
                    print(f"    🗑️ Deleted thumbnails:")
                    for thumb in deleted_thumbnails:
                        print(f"       {thumb}")
                else:
                    print(f"    📷 No thumbnail files found")
                
                # Delete the film from database
                film.delete()
                print(f"    ✅ Removed film from database")
                self.stats['films_removed'] += 1
                
            except Film.DoesNotExist:
                print(f"    ⚠️ Film not found in database: {file_id}")
                self.stats['films_not_found'] += 1
                
                # Still try to delete any orphaned thumbnails
                deleted_thumbnails = self.find_and_delete_thumbnails(file_id)
                if deleted_thumbnails:
                    print(f"    🗑️ Deleted orphaned thumbnails:")
                    for thumb in deleted_thumbnails:
                        print(f"       {thumb}")
                        
            except Exception as e:
                print(f"    ❌ Error processing {file_id}: {e}")
                self.stats['errors'] += 1
            
            print()  # Empty line for readability

    def print_summary(self):
        """Print removal summary"""
        print("=" * 60)
        print("FILM REMOVAL SUMMARY")
        print("=" * 60)
        print(f"Films processed: {len(self.films_to_remove)}")
        print(f"Films removed: {self.stats['films_removed']}")
        print(f"Films not found: {self.stats['films_not_found']}")
        print(f"Thumbnails deleted: {self.stats['thumbnails_deleted']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    print("=== FILM REMOVAL SCRIPT ===\n")
    
    remover = FilmRemover()
    
    # Confirm removal
    print(f"About to remove {len(remover.films_to_remove)} films:")
    for file_id in remover.films_to_remove:
        print(f"  - {file_id}")
    print()
    
    remover.remove_films()
    remover.print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())