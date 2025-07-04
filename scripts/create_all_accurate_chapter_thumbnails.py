#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_accurate_chapter_thumbnails_for_film(film):
    """Create accurate individual chapter thumbnails for a single film"""
    
    chapters = film.chapters.all().order_by('order')
    
    if not chapters.exists():
        print(f"    ⚠️ No chapters found, skipping")
        return 0
    
    print(f"    Creating {chapters.count()} individual chapter thumbnails...")
    
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
    
    chapters_dir = '/home/viblio/family_films/static/thumbnails/chapters'
    os.makedirs(chapters_dir, exist_ok=True)
    
    created_count = 0
    
    for i, chapter in enumerate(chapters):
        # Create thumbnail image (individual chapter thumbnail size)
        thumbnail_width, thumbnail_height = 80, 60
        thumbnail_image = Image.new('RGB', (thumbnail_width, thumbnail_height), chapter_colors[i % len(chapter_colors)])
        draw = ImageDraw.Draw(thumbnail_image)
        
        # Load fonts
        try:
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 7)
        except:
            time_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw timestamp prominently at top
        timestamp_text = chapter.start_time
        time_bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (thumbnail_width - time_width) // 2
        
        # Background for timestamp
        draw.rectangle([time_x-2, 2, time_x+time_width+2, 14], fill=(0, 0, 0, 200))
        draw.text((time_x, 3), timestamp_text, fill=(255, 255, 255), font=time_font)
        
        # Draw chapter number
        chapter_num = f"Ch. {i+1}"
        draw.text((3, 16), chapter_num, fill=(255, 255, 255), font=title_font)
        
        # Draw chapter title (wrapped to fit)
        title_words = chapter.title.split()
        title_lines = []
        current_line = []
        
        for word in title_words:
            test_line = ' '.join(current_line + [word])
            test_bbox = draw.textbbox((0, 0), test_line, font=small_font)
            test_width = test_bbox[2] - test_bbox[0]
            
            if test_width <= thumbnail_width - 6:
                current_line.append(word)
            else:
                if current_line:
                    title_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    title_lines.append(word)
        
        if current_line:
            title_lines.append(' '.join(current_line))
        
        # Draw title lines (max 3 lines for small thumbnail)
        y_offset = 28
        for line in title_lines[:3]:
            if y_offset < thumbnail_height - 8:
                draw.text((3, y_offset), line, fill=(255, 255, 255), font=small_font)
                y_offset += 8
        
        # Add border
        draw.rectangle([0, 0, thumbnail_width-1, thumbnail_height-1], outline=(255, 255, 255), width=1)
        
        # Save individual thumbnail
        thumbnail_filename = f'{film.file_id}_{chapter.id}.jpg'
        thumbnail_path = os.path.join(chapters_dir, thumbnail_filename)
        
        # Backup existing file if it exists
        if os.path.exists(thumbnail_path):
            backup_path = thumbnail_path.replace('.jpg', '_backup.jpg')
            shutil.copy2(thumbnail_path, backup_path)
        
        thumbnail_image.save(thumbnail_path, 'JPEG', quality=90)
        thumbnail_image.close()
        
        # Update chapter thumbnail URL in database
        chapter.thumbnail_url = f'/static/thumbnails/chapters/{thumbnail_filename}'
        chapter.save()
        
        created_count += 1
    
    print(f"      ✅ Created {created_count} chapter thumbnails")
    return created_count

def create_all_accurate_chapter_thumbnails():
    """Create accurate individual chapter thumbnails for all films"""
    
    print("=== Creating Accurate Individual Chapter Thumbnails for All Films ===\n")
    
    # Get all films that have chapters
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct().order_by('file_id')
    
    print(f"Found {films_with_chapters.count()} films with chapters")
    
    if not films_with_chapters.exists():
        print("❌ No films with chapters found")
        return False
    
    total_thumbnails = 0
    success_count = 0
    error_count = 0
    
    for i, film in enumerate(films_with_chapters, 1):
        print(f"\n[{i}/{films_with_chapters.count()}] {film.file_id}: {film.title[:50]}...")
        
        try:
            thumbnails_created = create_accurate_chapter_thumbnails_for_film(film)
            if thumbnails_created > 0:
                success_count += 1
                total_thumbnails += thumbnails_created
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            error_count += 1
    
    print(f"\n=== Chapter Thumbnail Generation Summary ===")
    print(f"✅ Films processed: {success_count}")
    print(f"📊 Total thumbnails created: {total_thumbnails}")
    print(f"❌ Films with errors: {error_count}")
    print(f"📈 Total films with chapters: {films_with_chapters.count()}")
    
    return success_count > 0

if __name__ == '__main__':
    create_all_accurate_chapter_thumbnails()