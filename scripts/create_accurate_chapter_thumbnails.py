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

def create_accurate_chapter_thumbnails():
    """Create accurate individual chapter thumbnails for P-61_FROS"""
    
    print("=== Creating Accurate Individual Chapter Thumbnails ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📊 Creating individual thumbnails for {chapters.count()} chapters")
        
        # Color scheme for different chapter types
        chapter_colors = [
            (65, 105, 225),   # Royal Blue
            (34, 139, 34),    # Forest Green  
            (220, 20, 60),    # Crimson
            (255, 140, 0),    # Dark Orange
            (138, 43, 226),   # Blue Violet
            (0, 139, 139),    # Dark Cyan
        ]
        
        chapters_dir = '/home/viblio/family_films/static/thumbnails/chapters'
        os.makedirs(chapters_dir, exist_ok=True)
        
        for i, chapter in enumerate(chapters):
            print(f"   Creating thumbnail {i+1}: {chapter.start_time} - {chapter.title[:30]}...")
            
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
                import shutil
                shutil.copy2(thumbnail_path, backup_path)
                print(f"      📦 Backed up existing thumbnail to: {backup_path}")
            
            thumbnail_image.save(thumbnail_path, 'JPEG', quality=90)
            thumbnail_image.close()
            
            print(f"      ✅ Created: {thumbnail_filename} ({os.path.getsize(thumbnail_path):,} bytes)")
        
        print(f"\n✅ All individual chapter thumbnails created!")
        print(f"📁 Location: {chapters_dir}")
        print(f"🧪 Test at: http://127.0.0.1:8000/films/P-61_FROS/")
        print(f"   Chapter thumbnails should now show accurate placeholders")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error creating chapter thumbnails: {e}")
        return False

if __name__ == '__main__':
    create_accurate_chapter_thumbnails()