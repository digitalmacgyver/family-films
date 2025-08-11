#!/usr/bin/env python3
"""
Update RLD-R01_FROS

Updates the RLD-R01_FROS film with the correct YouTube ID and downloads its thumbnail.
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

from main.models import Film

class RLD_R01_Updater:
    def __init__(self):
        self.file_id = "RLD-R01_FROS"
        self.youtube_id = "0Y3zJjOZcko"
        self.youtube_url = f"https://www.youtube.com/watch?v={self.youtube_id}"

    def download_thumbnail(self):
        """Download thumbnail from YouTube"""
        try:
            thumbnail_dir = Path('/home/viblio/family_films/main/static/main/thumbnails')
            thumbnail_dir.mkdir(exist_ok=True)
            
            output_path = thumbnail_dir / f"{self.file_id}.jpg"
            
            print(f"📥 Downloading thumbnail for {self.youtube_id}...")
            
            cmd = [
                'yt-dlp',
                '--write-thumbnail',
                '--skip-download',
                '--no-warnings',
                '--quiet',
                '-o', str(thumbnail_dir / f"{self.youtube_id}.%(ext)s"),
                self.youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Find the downloaded thumbnail (it might have different extensions)
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    downloaded_file = thumbnail_dir / f"{self.youtube_id}.{ext}"
                    if downloaded_file.exists():
                        # Rename to the desired filename
                        if downloaded_file != output_path:
                            if output_path.exists():
                                output_path.unlink()  # Remove existing file
                            downloaded_file.rename(output_path)
                        
                        print(f"    ✅ Downloaded: {output_path}")
                        return True
                
                print(f"    ⚠️ Downloaded but couldn't find file for: {self.youtube_id}")
                return False
            else:
                print(f"    ❌ Failed to download thumbnail")
                print(f"       Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error downloading thumbnail: {e}")
            return False

    def update_film_record(self):
        """Update the film record with correct YouTube info"""
        try:
            film = Film.objects.get(file_id=self.file_id)
            
            print(f"📽️ Found film: {film.title or 'Untitled'}")
            print(f"    Current YouTube ID: {film.youtube_id}")
            print(f"    Current thumbnail: {film.thumbnail_url}")
            
            # Update YouTube ID and URL
            old_youtube_id = film.youtube_id
            film.youtube_id = self.youtube_id
            film.youtube_url = self.youtube_url
            
            # Update thumbnail URL to use YouTube's thumbnail
            new_thumbnail_url = f"https://img.youtube.com/vi/{self.youtube_id}/maxresdefault.jpg"
            old_thumbnail_url = film.thumbnail_url
            film.thumbnail_url = new_thumbnail_url
            
            film.save()
            
            print(f"    ✅ Updated film record:")
            print(f"       YouTube ID: {old_youtube_id} → {self.youtube_id}")
            print(f"       Thumbnail: {old_thumbnail_url} → {new_thumbnail_url}")
            
            return True
            
        except Film.DoesNotExist:
            print(f"    ❌ Film not found: {self.file_id}")
            return False
        except Exception as e:
            print(f"    ❌ Error updating film: {e}")
            return False

    def get_video_info(self):
        """Get video information from YouTube"""
        try:
            print(f"📺 Getting video info for {self.youtube_id}...")
            
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--skip-download',
                '--no-warnings',
                '--quiet',
                self.youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                video_data = json.loads(result.stdout)
                title = video_data.get('title', 'Unknown')
                description = video_data.get('description', '')
                
                print(f"    🎬 Title: {title}")
                print(f"    📝 Description length: {len(description)} chars")
                
                # Check if File ID is in description
                if f"File ID: {self.file_id}" in description:
                    print(f"    ✅ Confirmed File ID {self.file_id} found in description")
                else:
                    print(f"    ⚠️ File ID {self.file_id} not found in description")
                
                return True
            else:
                print(f"    ❌ Failed to get video info: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"    ❌ Error getting video info: {e}")
            return False

def main():
    print("=== RLD-R01_FROS UPDATER ===\n")
    
    updater = RLD_R01_Updater()
    
    print(f"Processing: {updater.file_id}")
    print(f"YouTube URL: {updater.youtube_url}")
    print()
    
    # Get video info to confirm it's the right video
    if not updater.get_video_info():
        print("❌ Could not verify video info")
        return 1
    
    print()
    
    # Download thumbnail
    thumbnail_success = updater.download_thumbnail()
    
    print()
    
    # Update film record
    film_success = updater.update_film_record()
    
    print()
    
    if thumbnail_success and film_success:
        print("✅ Successfully updated RLD-R01_FROS with YouTube thumbnail")
        return 0
    else:
        print("⚠️ Update completed with some issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())