#!/usr/bin/env python3
"""
Update Batch D Thumbnails

Simple script to download thumbnails for mapped Batch D films and update film records.
"""

import os
import sys
import django
import json
import requests

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def download_thumbnail(url, file_path):
    """Download thumbnail image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"      ✅ Downloaded: {os.path.basename(file_path)}")
        return True
        
    except Exception as e:
        print(f"      ❌ Error downloading {url}: {e}")
        return False

def main():
    print("=== BATCH D THUMBNAIL UPDATER ===\n")
    
    # Load mapping file
    mapping_file = '/home/viblio/family_films/scripts/batch_d_video_mapping.json'
    
    try:
        with open(mapping_file, 'r') as f:
            mappings = json.load(f)
    except Exception as e:
        print(f"❌ Error loading mapping file: {e}")
        return 1
    
    thumbnails_dir = '/home/viblio/family_films/static/thumbnails/films'
    stats = {'processed': 0, 'downloaded': 0, 'errors': 0}
    
    for mapping in mappings:
        file_id = mapping['file_id']
        youtube_id = mapping['youtube_id']
        title = mapping['title']
        
        stats['processed'] += 1
        print(f"[{stats['processed']}/{len(mappings)}] Processing: {file_id}")
        
        try:
            # Get the film record
            film = Film.objects.get(file_id=file_id)
            
            # Download thumbnail
            thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg"
            thumbnail_filename = f"{file_id}_maxres.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            print(f"    📥 Downloading thumbnail from YouTube...")
            
            success = download_thumbnail(thumbnail_url, thumbnail_path)
            
            if not success:
                # Fallback to hqdefault
                print(f"    🔄 Trying hqdefault...")
                thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
                success = download_thumbnail(thumbnail_url, thumbnail_path)
            
            if success:
                stats['downloaded'] += 1
                
                # Update film record
                film.youtube_id = youtube_id
                film.youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
                film.thumbnail_url = f"/static/thumbnails/films/{thumbnail_filename}"
                film.thumbnail_high_url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
                film.thumbnail_medium_url = f"https://img.youtube.com/vi/{youtube_id}/mqdefault.jpg"
                film.save()
                
                print(f"    ✅ Updated film: {film.title}")
            else:
                print(f"    ❌ Failed to download thumbnail")
                stats['errors'] += 1
                
        except Film.DoesNotExist:
            print(f"    ❌ Film not found: {file_id}")
            stats['errors'] += 1
        except Exception as e:
            print(f"    ❌ Error processing {file_id}: {str(e)}")
            stats['errors'] += 1
        
        print()  # Add spacing
    
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Films processed: {stats['processed']}")
    print(f"Thumbnails downloaded: {stats['downloaded']}")
    print(f"Errors: {stats['errors']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())