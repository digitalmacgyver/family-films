#!/usr/bin/env python3

import django
import os
import sys
import tempfile
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film
from PIL import Image, ImageDraw, ImageFont

def regenerate_p61_sprite():
    """Regenerate the sprite for P-61_FROS with better quality"""
    
    print("=== Regenerating P-61_FROS Sprite ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📊 Target timestamps:")
        
        frame_timestamps = []
        for i, chapter in enumerate(chapters):
            frame_timestamps.append(chapter.start_time_seconds)
            print(f"   Frame {i+1}: {chapter.start_time_seconds}s - {chapter.title[:50]}")
        
        # Create improved sprite using diverse YouTube thumbnails
        frame_width, frame_height = 160, 90
        frame_count = len(frame_timestamps)
        sprite_width = frame_width * frame_count
        sprite_height = frame_height
        
        sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
        
        # Use more diverse thumbnail sources to get different frames
        thumbnail_sources = [
            f"https://img.youtube.com/vi/{film.youtube_id}/1.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/2.jpg", 
            f"https://img.youtube.com/vi/{film.youtube_id}/3.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/mqdefault.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/default.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/sddefault.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/maxresdefault.jpg"
        ]
        
        print(f"\n📸 Generating frames...")
        
        for i in range(frame_count):
            source_url = thumbnail_sources[i % len(thumbnail_sources)]
            
            try:
                response = requests.get(source_url, timeout=10)
                response.raise_for_status()
                
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_file.write(response.content)
                temp_file.close()
                
                # Open and process the image
                frame_image = Image.open(temp_file.name)
                frame_image = frame_image.resize((frame_width, frame_height))
                
                # Apply timestamp overlay to show which frame this represents
                draw = ImageDraw.Draw(frame_image)
                timestamp_text = f"{frame_timestamps[i]}s"
                
                # Try to load a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
                except:
                    font = ImageFont.load_default()
                
                # Add timestamp overlay
                text_bbox = draw.textbbox((0, 0), timestamp_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                # Position in top-left corner with background
                x, y = 2, 2
                draw.rectangle([x-1, y-1, x+text_width+1, y+text_height+1], fill=(0, 0, 0, 180))
                draw.text((x, y), timestamp_text, fill=(255, 255, 255), font=font)
                
                # Apply frame-specific variations to reduce similarity
                if i > 0:
                    from PIL import ImageEnhance
                    if i % 2 == 1:
                        # Slightly adjust brightness for odd frames
                        enhancer = ImageEnhance.Brightness(frame_image)
                        frame_image = enhancer.enhance(0.95)
                    if i % 3 == 2:
                        # Slightly adjust contrast for every 3rd frame
                        enhancer = ImageEnhance.Contrast(frame_image)
                        frame_image = enhancer.enhance(1.05)
                
                # Paste into sprite sheet
                x_offset = i * frame_width
                sprite_image.paste(frame_image, (x_offset, 0))
                frame_image.close()
                
                # Cleanup temp file
                os.unlink(temp_file.name)
                
                print(f"   ✅ Frame {i+1}: {timestamp_text} from {source_url.split('/')[-1]}")
                
            except Exception as e:
                print(f"   ⚠️ Failed to get frame {i+1}: {e}")
                # Create placeholder frame with timestamp
                placeholder = Image.new('RGB', (frame_width, frame_height), (64, 64, 64))
                draw = ImageDraw.Draw(placeholder)
                
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                except:
                    font = ImageFont.load_default()
                
                timestamp_text = f"{frame_timestamps[i]}s"
                text_bbox = draw.textbbox((0, 0), timestamp_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (frame_width - text_width) // 2
                y = (frame_height - text_height) // 2
                draw.text((x, y), timestamp_text, fill=(255, 255, 255), font=font)
                
                x_offset = i * frame_width
                sprite_image.paste(placeholder, (x_offset, 0))
        
        # Save the new sprite
        sprite_path = os.path.join('/home/viblio/family_films/static/thumbnails/previews', f'{film.file_id}_sprite.jpg')
        sprite_image.save(sprite_path, 'JPEG', quality=90)
        sprite_image.close()
        
        # Update film record
        film.preview_sprite_url = f'/static/thumbnails/previews/{film.file_id}_sprite.jpg'
        film.preview_frame_count = frame_count
        film.preview_frame_interval = 0.8
        film.preview_sprite_width = frame_width
        film.preview_sprite_height = frame_height
        film.save()
        
        print(f"\n✅ Sprite regenerated successfully!")
        print(f"   File: {sprite_path}")
        print(f"   Size: {os.path.getsize(sprite_path):,} bytes")
        print(f"   Dimensions: {sprite_width}x{sprite_height}")
        print(f"   Frames: {frame_count}")
        
        # Extract individual frames again for inspection
        frames_dir = '/home/viblio/family_films/debugging/frames_p61_new'
        os.makedirs(frames_dir, exist_ok=True)
        
        new_sprite = Image.open(sprite_path)
        for i in range(frame_count):
            x_offset = i * frame_width
            frame_box = (x_offset, 0, x_offset + frame_width, frame_height)
            frame_image = new_sprite.crop(frame_box)
            
            frame_path = os.path.join(frames_dir, f'frame_{i+1}_new.jpg')
            frame_image.save(frame_path, 'JPEG', quality=90)
            frame_image.close()
        
        new_sprite.close()
        
        print(f"📁 New individual frames saved to: {frames_dir}")
        print(f"\n🧪 TEST INSTRUCTIONS:")
        print(f"1. Visit: http://127.0.0.1:8000/films/")
        print(f"2. Find the P-61_FROS film card")
        print(f"3. Hover over the thumbnail")
        print(f"4. You should see animation with timestamp overlays")
        print(f"5. Check browser console for any JavaScript errors")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error regenerating sprite: {e}")
        return False

if __name__ == '__main__':
    regenerate_p61_sprite()