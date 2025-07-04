#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def find_thumbnail_location():
    """Find where animated thumbnail images are stored for PB-14_FROS"""
    
    print("=== Finding Thumbnail Location for PB-14_FROS ===\n")
    
    try:
        film = Film.objects.get(file_id='PB-14_FROS')
        print(f"Film: {film.title}")
        print(f"File ID: {film.file_id}")
        print(f"YouTube ID: {film.youtube_id}")
        
        print(f"\n--- Thumbnail URLs ---")
        print(f"Main thumbnail: {film.thumbnail_url}")
        print(f"High quality: {film.thumbnail_high_url}")
        print(f"Medium quality: {film.thumbnail_medium_url}")
        
        print(f"\n--- Animated Thumbnail Data ---")
        print(f"Preview sprite URL: {film.preview_sprite_url}")
        print(f"Frame count: {film.preview_frame_count}")
        print(f"Frame interval: {film.preview_frame_interval}")
        print(f"Sprite width: {film.preview_sprite_width}")
        print(f"Sprite height: {film.preview_sprite_height}")
        print(f"Has animated thumbnail: {film.has_animated_thumbnail()}")
        
        # Check if it's a local file path or URL
        if film.preview_sprite_url:
            print(f"\n--- Analyzing Sprite URL ---")
            sprite_url = film.preview_sprite_url
            print(f"Sprite URL: {sprite_url}")
            
            if sprite_url.startswith('http'):
                print("✓ This is a web URL (hosted externally)")
            elif sprite_url.startswith('/'):
                print("✓ This is a local file path")
                # Check if file exists locally
                local_path = sprite_url.lstrip('/')
                full_path = os.path.join('/home/viblio/family_films', local_path)
                print(f"Local file path: {full_path}")
                
                if os.path.exists(full_path):
                    print("✓ File exists locally")
                    file_size = os.path.getsize(full_path)
                    print(f"File size: {file_size:,} bytes")
                else:
                    print("✗ File does not exist at this location")
                    
                    # Search for the file in common locations
                    search_locations = [
                        '/home/viblio/family_films/static/',
                        '/home/viblio/family_films/media/',
                        '/home/viblio/family_films/thumbnails/',
                        '/home/viblio/family_films/static/thumbnails/',
                        '/home/viblio/family_films/static/images/',
                    ]
                    
                    filename = os.path.basename(sprite_url)
                    print(f"\nSearching for file: {filename}")
                    
                    for location in search_locations:
                        potential_path = os.path.join(location, filename)
                        if os.path.exists(potential_path):
                            print(f"✓ Found at: {potential_path}")
                        else:
                            print(f"✗ Not found at: {potential_path}")
            else:
                print("✓ This is a relative path")
                
        else:
            print("No preview sprite URL found")
            
    except Film.DoesNotExist:
        print("Film with file_id 'PB-14_FROS' not found")
        
        # Show available films
        print("\nAvailable films:")
        films = Film.objects.all()[:10]
        for film in films:
            print(f"- {film.file_id}: {film.title}")

if __name__ == '__main__':
    find_thumbnail_location()