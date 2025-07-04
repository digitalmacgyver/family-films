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
import textwrap

def create_accurate_placeholder_sprite():
    """Create accurate placeholder sprite for P-61_FROS with chapter information"""
    
    print("=== Creating Accurate Placeholder Sprite ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📊 Creating informative placeholders for {chapters.count()} chapters")
        
        # Create sprite with chapter information
        frame_width, frame_height = 160, 90
        sprite_width = frame_width * chapters.count()
        sprite_height = frame_height
        
        sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
        
        # Color scheme for different chapter types
        chapter_colors = [
            (65, 105, 225),   # Royal Blue
            (34, 139, 34),    # Forest Green  
            (220, 20, 60),    # Crimson
            (255, 140, 0),    # Dark Orange
            (138, 43, 226),   # Blue Violet
            (0, 139, 139),    # Dark Cyan
        ]
        
        for i, chapter in enumerate(chapters):
            print(f"   Creating frame {i+1}: {chapter.start_time} - {chapter.title[:30]}...")
            
            # Create frame image
            frame_image = Image.new('RGB', (frame_width, frame_height), chapter_colors[i % len(chapter_colors)])
            draw = ImageDraw.Draw(frame_image)
            
            # Load font
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
        sprite_path = os.path.join('/home/viblio/family_films/static/thumbnails/previews', f'{film.file_id}_sprite_accurate.jpg')
        sprite_image.save(sprite_path, 'JPEG', quality=90)
        sprite_image.close()
        
        print(f"\n✅ Accurate placeholder sprite created!")
        print(f"   Path: {sprite_path}")
        print(f"   Size: {os.path.getsize(sprite_path):,} bytes")
        
        # Create a side-by-side comparison image
        comparison_path = os.path.join('/home/viblio/family_films/debugging', 'sprite_comparison.jpg')
        create_sprite_comparison(film, sprite_path, comparison_path)
        
        print(f"📊 Comparison image: {comparison_path}")
        
        # Update film record to use this sprite temporarily
        print("\nReplacing current sprite with accurate placeholder...")
        choice = 'y'
        if choice == 'y':
            # Backup old sprite
            old_sprite_path = film.preview_sprite_url.lstrip('/')
            old_full_path = os.path.join('/home/viblio/family_films', old_sprite_path)
            backup_path = old_full_path.replace('.jpg', '_backup.jpg')
            
            if os.path.exists(old_full_path):
                import shutil
                shutil.copy2(old_full_path, backup_path)
                print(f"📦 Backed up old sprite to: {backup_path}")
            
            # Replace with new sprite
            new_sprite_path = os.path.join('/home/viblio/family_films/static/thumbnails/previews', f'{film.file_id}_sprite.jpg')
            import shutil
            shutil.copy2(sprite_path, new_sprite_path)
            
            print(f"✅ Replaced sprite with accurate placeholder")
            print(f"🧪 Test at: http://127.0.0.1:8000/films/")
            print(f"   Hover over P-61_FROS thumbnail to see informative frames")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error creating placeholder sprite: {e}")
        return False

def create_sprite_comparison(film, new_sprite_path, comparison_path):
    """Create a side-by-side comparison of old vs new sprite"""
    
    try:
        old_sprite_path = film.preview_sprite_url.lstrip('/')
        old_full_path = os.path.join('/home/viblio/family_films', old_sprite_path)
        
        if not os.path.exists(old_full_path):
            print("⚠️ Old sprite not found for comparison")
            return
        
        # Load both sprites
        old_sprite = Image.open(old_full_path)
        new_sprite = Image.open(new_sprite_path)
        
        # Create comparison image
        old_width, old_height = old_sprite.size
        new_width, new_height = new_sprite.size
        
        comparison_width = max(old_width, new_width)
        comparison_height = old_height + new_height + 60  # Extra space for labels
        
        comparison = Image.new('RGB', (comparison_width, comparison_height), (240, 240, 240))
        
        # Paste old sprite
        comparison.paste(old_sprite, (0, 20))
        
        # Paste new sprite
        comparison.paste(new_sprite, (0, old_height + 40))
        
        # Add labels
        draw = ImageDraw.Draw(comparison)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 5), "OLD: Misleading frames from wrong timestamps", fill=(255, 0, 0), font=font)
        draw.text((10, old_height + 25), "NEW: Accurate chapter information placeholders", fill=(0, 128, 0), font=font)
        
        comparison.save(comparison_path, 'JPEG', quality=90)
        comparison.close()
        old_sprite.close()
        new_sprite.close()
        
        print(f"📊 Created comparison image")
        
    except Exception as e:
        print(f"⚠️ Could not create comparison: {e}")

if __name__ == '__main__':
    create_accurate_placeholder_sprite()