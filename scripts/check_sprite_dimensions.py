#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def check_sprite_dimensions():
    """Check the sprite dimensions for P-61_FROS"""
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        
        print("=== P-61_FROS Sprite Dimensions ===")
        print(f"Film: {film.title}")
        print(f"File ID: {film.file_id}")
        print()
        
        print("Current database values:")
        print(f"  preview_sprite_url: {film.preview_sprite_url}")
        print(f"  preview_sprite_width: {film.preview_sprite_width}")
        print(f"  preview_sprite_height: {film.preview_sprite_height}")
        print(f"  preview_frame_count: {film.preview_frame_count}")
        print(f"  preview_frame_interval: {film.preview_frame_interval}")
        print()
        
        # Check actual sprite file dimensions
        sprite_path = os.path.join('/home/viblio/family_films', film.preview_sprite_url.lstrip('/'))
        if os.path.exists(sprite_path):
            from PIL import Image
            with Image.open(sprite_path) as img:
                actual_width, actual_height = img.size
                print(f"Actual sprite file dimensions:")
                print(f"  Total width: {actual_width}px")
                print(f"  Total height: {actual_height}px")
                print(f"  Frame count: {film.preview_frame_count}")
                print(f"  Calculated frame width: {actual_width / film.preview_frame_count:.1f}px")
                print()
                
                # Check if dimensions match
                expected_frame_width = actual_width / film.preview_frame_count
                current_sprite_width = film.preview_sprite_width
                
                print("Analysis:")
                if abs(expected_frame_width - current_sprite_width) < 1:
                    print("  ✅ Sprite width is correct")
                else:
                    print(f"  ❌ Sprite width mismatch!")
                    print(f"     Database has: {current_sprite_width}px per frame")
                    print(f"     Should be: {expected_frame_width:.1f}px per frame")
                    print(f"     Fix: Update preview_sprite_width to {expected_frame_width:.0f}")
        else:
            print(f"❌ Sprite file not found: {sprite_path}")
            
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    check_sprite_dimensions()