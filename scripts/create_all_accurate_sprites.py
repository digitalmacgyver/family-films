#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_accurate_sprite_for_film(film):
    """Create accurate placeholder sprite for a single film"""
    
    chapters = film.chapters.all().order_by('order')
    
    if not chapters.exists():
        print(f"    ⚠️ No chapters found, skipping")
        return False
    
    print(f"    Creating sprite for {chapters.count()} chapters...")
    
    # Color scheme for different chapter types
    chapter_colors = [
        (65, 105, 225),   # Royal Blue
        (34, 139, 34),    # Forest Green  
        (220, 20, 60),    # Crimson
        (255, 140, 0),    # Dark Orange
        (138, 43, 226),   # Blue Violet
        (0, 139, 139),    # Dark Cyan
        (255, 20, 147),   # Deep Pink
        (30, 144, 255),   # Dodger Blue
        (255, 165, 0),    # Orange
        (50, 205, 50),    # Lime Green
    ]
    
    # Create sprite with chapter information
    frame_width, frame_height = 160, 90
    sprite_width = frame_width * chapters.count()
    sprite_height = frame_height
    
    sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
    
    for i, chapter in enumerate(chapters):
        # Create frame image
        frame_image = Image.new('RGB', (frame_width, frame_height), chapter_colors[i % len(chapter_colors)])
        draw = ImageDraw.Draw(frame_image)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw timestamp prominently at top
        timestamp_text = chapter.start_time
        time_bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (frame_width - time_width) // 2
        
        # Background for timestamp
        draw.rectangle([time_x-3, 3, time_x+time_width+3, 23], fill=(0, 0, 0, 200))
        draw.text((time_x, 5), timestamp_text, fill=(255, 255, 255), font=time_font)
        
        # Draw chapter number
        chapter_num = f"Ch. {i+1}"
        draw.text((5, 25), chapter_num, fill=(255, 255, 255), font=title_font)
        
        # Draw chapter title (wrapped)
        title_words = chapter.title.split()
        title_lines = []
        current_line = []
        
        for word in title_words:
            test_line = ' '.join(current_line + [word])
            test_bbox = draw.textbbox((0, 0), test_line, font=small_font)
            test_width = test_bbox[2] - test_bbox[0]
            
            if test_width <= frame_width - 10:
                current_line.append(word)
            else:
                if current_line:
                    title_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    title_lines.append(word)
        
        if current_line:
            title_lines.append(' '.join(current_line))
        
        # Draw title lines (max 4 lines)
        y_offset = 45
        for line in title_lines[:4]:
            if y_offset < frame_height - 15:
                draw.text((5, y_offset), line, fill=(255, 255, 255), font=small_font)
                y_offset += 12
        
        # Add border
        draw.rectangle([0, 0, frame_width-1, frame_height-1], outline=(255, 255, 255), width=2)
        
        # Paste into sprite
        x_offset = i * frame_width
        sprite_image.paste(frame_image, (x_offset, 0))
    
    # Save sprite
    previews_dir = '/home/viblio/family_films/static/thumbnails/previews'
    os.makedirs(previews_dir, exist_ok=True)
    
    sprite_path = os.path.join(previews_dir, f'{film.file_id}_sprite.jpg')
    
    # Backup existing sprite if it exists
    if os.path.exists(sprite_path):
        backup_path = sprite_path.replace('.jpg', '_backup.jpg')
        shutil.copy2(sprite_path, backup_path)
        print(f"      📦 Backed up existing sprite")
    
    sprite_image.save(sprite_path, 'JPEG', quality=90)
    sprite_image.close()
    
    print(f"      ✅ Created sprite: {os.path.getsize(sprite_path):,} bytes")
    
    # Update film sprite metadata
    film.preview_sprite_width = frame_width
    film.preview_sprite_height = frame_height
    film.preview_frame_count = chapters.count()
    film.save()
    
    return True

def create_all_accurate_sprites():
    """Create accurate placeholder sprites for all films"""
    
    print("=== Creating Accurate Placeholder Sprites for All Films ===\n")
    
    # Get all films that have chapters
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct().order_by('file_id')
    
    print(f"Found {films_with_chapters.count()} films with chapters")
    
    if not films_with_chapters.exists():
        print("❌ No films with chapters found")
        return False
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, film in enumerate(films_with_chapters, 1):
        print(f"\n[{i}/{films_with_chapters.count()}] {film.file_id}: {film.title[:50]}...")
        
        try:
            if create_accurate_sprite_for_film(film):
                success_count += 1
            else:
                skip_count += 1
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            error_count += 1
    
    print(f"\n=== Sprite Generation Summary ===")
    print(f"✅ Created: {success_count} sprites")
    print(f"⚠️ Skipped: {skip_count} films")
    print(f"❌ Errors: {error_count} films")
    print(f"📊 Total processed: {films_with_chapters.count()} films")
    
    return success_count > 0

if __name__ == '__main__':
    create_all_accurate_sprites()