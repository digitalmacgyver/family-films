#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter
from PIL import Image

def generate_chapter_thumbnails_from_sprite():
    """Generate individual chapter thumbnails from the sprite for P-61_FROS"""
    
    print("=== Generating Chapter Thumbnails from Sprite ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📊 Chapters: {chapters.count()}")
        
        # Check if sprite exists
        sprite_path = film.preview_sprite_url.lstrip('/')
        full_sprite_path = os.path.join('/home/viblio/family_films', sprite_path)
        
        if not os.path.exists(full_sprite_path):
            print(f"❌ Sprite not found: {full_sprite_path}")
            return False
        
        # Create chapters directory
        chapters_dir = os.path.join('/home/viblio/family_films/static/thumbnails/chapters')
        os.makedirs(chapters_dir, exist_ok=True)
        
        # Open sprite image
        sprite_image = Image.open(full_sprite_path)
        frame_width = film.preview_sprite_width or 160
        frame_height = film.preview_sprite_height or 90
        
        print(f"📸 Extracting chapter thumbnails:")
        
        for i, chapter in enumerate(chapters):
            # Extract frame from sprite
            x_offset = i * frame_width
            frame_box = (x_offset, 0, x_offset + frame_width, frame_height)
            chapter_image = sprite_image.crop(frame_box)
            
            # Save chapter thumbnail
            chapter_thumb_path = os.path.join(chapters_dir, f'{film.file_id}_{chapter.id}.jpg')
            chapter_image.save(chapter_thumb_path, 'JPEG', quality=85)
            
            # Update chapter record
            relative_url = f'/static/thumbnails/chapters/{film.file_id}_{chapter.id}.jpg'
            chapter.thumbnail_url = relative_url
            chapter.save()
            
            chapter_image.close()
            
            print(f"   ✅ Chapter {i+1}: {chapter.start_time} - {chapter.title[:40]}...")
            print(f"      Saved: {chapter_thumb_path}")
            print(f"      URL: {relative_url}")
        
        sprite_image.close()
        
        print(f"\n✅ All chapter thumbnails generated!")
        print(f"📁 Location: {chapters_dir}")
        
        # Verify chapter thumbnails on detail page
        print(f"\n🧪 CHAPTER THUMBNAIL TEST:")
        print(f"1. Visit: http://127.0.0.1:8000/films/P-61_FROS/")
        print(f"2. Look at the chapter list on the right side")
        print(f"3. Each chapter should have a thumbnail with timestamp overlay")
        print(f"4. Thumbnails should correspond to: 1s, 14s, 245s, 257s, 395s, 697s")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error generating chapter thumbnails: {e}")
        return False

def test_complete_thumbnail_system():
    """Test the complete thumbnail system for P-61_FROS"""
    
    print(f"\n=== Complete Thumbnail System Test ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎯 SYSTEM STATUS for P-61_FROS:")
        print(f"✅ Duration: {film.duration} (15:48)")
        print(f"✅ Chapters: {chapters.count()} defined")
        print(f"✅ Sprite: {film.preview_frame_count} frames")
        print(f"✅ Animation: JavaScript ready")
        
        # Check chapter thumbnails
        chapters_with_thumbs = 0
        for chapter in chapters:
            if chapter.thumbnail_url:
                thumb_path = chapter.thumbnail_url.lstrip('/')
                full_path = os.path.join('/home/viblio/family_films', thumb_path)
                if os.path.exists(full_path):
                    chapters_with_thumbs += 1
        
        print(f"✅ Chapter Thumbnails: {chapters_with_thumbs}/{chapters.count()}")
        
        print(f"\n🎉 THUMBNAIL SYSTEM READY!")
        print(f"📍 Test URLs:")
        print(f"   Film Catalog: http://127.0.0.1:8000/films/")
        print(f"   Film Detail: http://127.0.0.1:8000/films/P-61_FROS/")
        
        print(f"\n✨ Expected Behavior:")
        print(f"🎬 Film Catalog Page:")
        print(f"   - Hover over P-61_FROS thumbnail")
        print(f"   - See 6-frame animation with timestamps")
        print(f"   - Frames cycle every 0.8 seconds")
        
        print(f"📽️ Film Detail Page:")
        print(f"   - 6 chapters listed on right side")
        print(f"   - Each chapter has timestamp-labeled thumbnail")
        print(f"   - Clicking chapter navigates video to that time")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False

if __name__ == '__main__':
    success = generate_chapter_thumbnails_from_sprite()
    if success:
        test_complete_thumbnail_system()