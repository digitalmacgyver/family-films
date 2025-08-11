#!/usr/bin/env python3
"""
Create Default Thumbnails

Creates default placeholder thumbnails for Batch D films that don't have YouTube matches yet.
"""

import os
import sys
import django
from PIL import Image, ImageDraw, ImageFont

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def create_default_thumbnail(file_id, title, output_path):
    """Create a default thumbnail with film info"""
    # Create a 1280x720 image (YouTube maxresdefault size)
    width, height = 1280, 720
    img = Image.new('RGB', (width, height), color='#2c3e50')
    
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default if not available
    try:
        font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
        font_id = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
    except:
        font_title = ImageFont.load_default()
        font_id = ImageFont.load_default()
    
    # Draw file ID at top
    draw.text((width//2, 150), f"FILE ID: {file_id}", font=font_id, anchor='mm', fill='white')
    
    # Draw title (wrap text if too long)
    title_lines = []
    words = title.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] < width - 100:
            current_line = test_line
        else:
            if current_line:
                title_lines.append(current_line)
                current_line = word
            else:
                title_lines.append(word)
    
    if current_line:
        title_lines.append(current_line)
    
    # Draw title lines centered
    y_start = height//2 - (len(title_lines) * 60 // 2)
    for i, line in enumerate(title_lines[:4]):  # Max 4 lines
        draw.text((width//2, y_start + i * 60), line, font=font_title, anchor='mm', fill='#ecf0f1')
    
    # Draw "FAMILY FILMS" at bottom
    draw.text((width//2, height - 80), "FAMILY FILMS", font=font_id, anchor='mm', fill='#95a5a6')
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path, 'JPEG', quality=90)
    return True

def main():
    print("=== DEFAULT THUMBNAIL CREATOR ===\n")
    
    # Get Batch D films that still have placeholder YouTube IDs
    batch_d_films = Film.objects.filter(youtube_id__startswith='placeholder_').order_by('file_id')
    
    thumbnails_dir = '/home/viblio/family_films/static/thumbnails/films'
    stats = {'processed': 0, 'created': 0, 'errors': 0}
    
    print(f"Found {batch_d_films.count()} films needing default thumbnails\n")
    
    for film in batch_d_films:
        stats['processed'] += 1
        print(f"[{stats['processed']}/{batch_d_films.count()}] Creating thumbnail: {film.file_id}")
        
        try:
            thumbnail_filename = f"{film.file_id}_default.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            # Create default thumbnail
            success = create_default_thumbnail(film.file_id, film.title, thumbnail_path)
            
            if success:
                stats['created'] += 1
                
                # Update film record
                film.thumbnail_url = f"/static/thumbnails/films/{thumbnail_filename}"
                film.save()
                
                print(f"    ✅ Created default thumbnail: {thumbnail_filename}")
            else:
                stats['errors'] += 1
                
        except Exception as e:
            print(f"    ❌ Error creating thumbnail for {film.file_id}: {str(e)}")
            stats['errors'] += 1
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Films processed: {stats['processed']}")
    print(f"Thumbnails created: {stats['created']}")
    print(f"Errors: {stats['errors']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())