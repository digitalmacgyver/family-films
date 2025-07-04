#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def verify_new_thumbnails():
    """Verify the new thumbnail generation worked correctly"""
    
    print("=== Verifying New Thumbnail Generation ===\n")
    
    test_films = ['PA-03_FROS', 'PB-14_FROS']
    
    for file_id in test_films:
        try:
            film = Film.objects.get(file_id=file_id)
            chapters = film.chapters.all().order_by('order')
            
            print(f"🎬 FILM: {film.title}")
            print(f"   File ID: {file_id}")
            print(f"   Chapters: {chapters.count()}")
            
            print(f"\n📊 SPRITE INFO:")
            print(f"   Sprite URL: {film.preview_sprite_url}")
            print(f"   Frame count: {film.preview_frame_count}")
            print(f"   Frame interval: {film.preview_frame_interval}")
            print(f"   Frame size: {film.preview_sprite_width}x{film.preview_sprite_height}")
            
            # Check if sprite file exists
            if film.preview_sprite_url:
                sprite_path = film.preview_sprite_url.lstrip('/')
                full_path = os.path.join('/home/viblio/family_films', sprite_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"   ✅ Sprite file exists: {size:,} bytes")
                else:
                    print(f"   ❌ Sprite file missing: {full_path}")
            
            # Show first few chapter timestamps
            print(f"\n🕐 CHAPTER TIMESTAMPS:")
            for i, chapter in enumerate(chapters[:5]):
                print(f"   {i+1}. {chapter.start_time} ({chapter.start_time_seconds}s) - {chapter.title[:50]}")
            if chapters.count() > 5:
                print(f"   ... and {chapters.count() - 5} more")
            
            # Check the frame count vs chapter count alignment
            frame_chapter_ratio = film.preview_frame_count / chapters.count() if chapters.count() > 0 else 0
            print(f"\n📏 ALIGNMENT:")
            print(f"   Chapters: {chapters.count()}")
            print(f"   Sprite frames: {film.preview_frame_count}")
            print(f"   Alignment: {'✅ GOOD' if abs(frame_chapter_ratio - 1.0) < 0.5 else '⚠️ MISMATCH'}")
            
            print("\n" + "="*60 + "\n")
            
        except Film.DoesNotExist:
            print(f"❌ Film {file_id} not found")

if __name__ == '__main__':
    verify_new_thumbnails()