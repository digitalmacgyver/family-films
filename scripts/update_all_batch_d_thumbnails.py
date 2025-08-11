#!/usr/bin/env python3
"""
Update All Batch D Thumbnails

Downloads YouTube thumbnails for all mapped Batch D videos and updates
the Film records with proper thumbnail URLs.
"""

import os
import sys
import django
import json
import subprocess
from pathlib import Path

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

class BatchDThumbnailUpdater:
    def __init__(self):
        self.mapping_file = '/home/viblio/family_films/scripts/batch_d_video_mapping.json'
        self.mappings = []
        self.stats = {
            'thumbnails_downloaded': 0,
            'films_updated': 0,
            'errors': 0,
            'skipped': 0
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

    def download_thumbnail(self, youtube_id, filename):
        """Download thumbnail for a YouTube video"""
        try:
            thumbnail_dir = Path('/home/viblio/family_films/main/static/main/thumbnails')
            thumbnail_dir.mkdir(exist_ok=True)
            
            output_path = thumbnail_dir / filename
            
            # Skip if thumbnail already exists and is not a placeholder
            if output_path.exists():
                # Check if it's a placeholder by size (our placeholders are exactly 1280x720)
                import PIL.Image
                try:
                    with PIL.Image.open(output_path) as img:
                        if img.size != (1280, 720):  # Real YouTube thumbnails have different sizes
                            print(f"    ⏩ Real thumbnail already exists: {filename}")
                            self.stats['skipped'] += 1
                            return True
                except:
                    pass  # If we can't read it, download a new one
            
            cmd = [
                'yt-dlp',
                '--write-thumbnail',
                '--skip-download',
                '--no-warnings',
                '--quiet',
                '-o', str(thumbnail_dir / f"{youtube_id}.%(ext)s"),
                f'https://www.youtube.com/watch?v={youtube_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Find the downloaded thumbnail (it might have different extensions)
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    downloaded_file = thumbnail_dir / f"{youtube_id}.{ext}"
                    if downloaded_file.exists():
                        # Rename to the desired filename
                        if downloaded_file != output_path:
                            if output_path.exists():
                                output_path.unlink()  # Remove existing file
                            downloaded_file.rename(output_path)
                        
                        print(f"    ✅ Downloaded: {filename}")
                        self.stats['thumbnails_downloaded'] += 1
                        return True
                
                print(f"    ⚠️ Downloaded but couldn't find file for: {youtube_id}")
                return False
            else:
                print(f"    ❌ Failed to download thumbnail for: {youtube_id}")
                print(f"       Error: {result.stderr}")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            print(f"    ❌ Error downloading {youtube_id}: {e}")
            self.stats['errors'] += 1
            return False

    def update_film_record(self, file_id, thumbnail_filename):
        """Update Film record with new thumbnail"""
        try:
            film = Film.objects.get(file_id=file_id)
            
            # Update the thumbnail field
            new_thumbnail_url = f"main/thumbnails/{thumbnail_filename}"
            old_thumbnail = film.thumbnail
            film.thumbnail = new_thumbnail_url
            film.save()
            
            print(f"    📝 Updated Film: {file_id}")
            print(f"       Old: {old_thumbnail}")
            print(f"       New: {new_thumbnail_url}")
            
            self.stats['films_updated'] += 1
            return True
            
        except Film.DoesNotExist:
            print(f"    ⚠️ Film not found: {file_id}")
            return False
        except Exception as e:
            print(f"    ❌ Error updating film {file_id}: {e}")
            self.stats['errors'] += 1
            return False

    def process_all_mappings(self):
        """Process all video mappings"""
        print(f"🚀 Processing {len(self.mappings)} video mappings...\n")
        
        for i, mapping in enumerate(self.mappings, 1):
            file_id = mapping['file_id']
            youtube_id = mapping['youtube_id']
            title = mapping['title']
            
            print(f"[{i:2d}/{len(self.mappings)}] Processing: {file_id}")
            print(f"    📺 YouTube: {youtube_id}")
            print(f"    🎬 Title: {title[:60]}...")
            
            # Generate thumbnail filename
            thumbnail_filename = f"{file_id}.jpg"
            
            # Download thumbnail
            if self.download_thumbnail(youtube_id, thumbnail_filename):
                # Update film record
                self.update_film_record(file_id, thumbnail_filename)
            
            print()  # Empty line for readability

    def print_summary(self):
        """Print processing summary"""
        print("=" * 60)
        print("BATCH D THUMBNAIL UPDATE SUMMARY")
        print("=" * 60)
        print(f"Mappings processed: {len(self.mappings)}")
        print(f"Thumbnails downloaded: {self.stats['thumbnails_downloaded']}")
        print(f"Films updated: {self.stats['films_updated']}")
        print(f"Skipped (existing): {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    print("=== BATCH D THUMBNAIL UPDATER ===\n")
    
    updater = BatchDThumbnailUpdater()
    
    if not updater.load_mappings():
        return 1
    
    updater.process_all_mappings()
    updater.print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())