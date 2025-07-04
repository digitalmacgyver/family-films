#!/usr/bin/env python3

import django
import os
import sys
import subprocess
import tempfile
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film
from PIL import Image, ImageDraw, ImageFont

def extract_real_frames_p61():
    """Extract real frames from P-61_FROS at correct timestamps using yt-dlp + ffmpeg"""
    
    print("=== Extracting Real Frames for P-61_FROS ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📺 YouTube: https://www.youtube.com/watch?v={film.youtube_id}")
        print(f"⏱️ Duration: {film.duration}")
        
        timestamps = []
        for chapter in chapters:
            timestamps.append(chapter.start_time_seconds)
            print(f"   {chapter.start_time} ({chapter.start_time_seconds}s) - {chapter.title}")
        
        print(f"\n🔧 Step 1: Getting video stream URL...")
        
        # Use yt-dlp to get the actual video stream URL
        yt_dlp_cmd = [
            '/home/viblio/.local/bin/yt-dlp',
            '--get-url',
            '--format', 'best[height<=720][ext=mp4]',  # Get reasonable quality MP4
            f'https://www.youtube.com/watch?v={film.youtube_id}'
        ]
        
        try:
            result = subprocess.run(yt_dlp_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"❌ yt-dlp failed: {result.stderr}")
                return False
            
            video_url = result.stdout.strip()
            print(f"✅ Got video stream URL: {video_url[:100]}...")
            
        except subprocess.TimeoutExpired:
            print("❌ yt-dlp timed out")
            return False
        except Exception as e:
            print(f"❌ Error running yt-dlp: {e}")
            return False
        
        print(f"\n🔧 Step 2: Extracting frames at specific timestamps...")
        
        # Create temporary directory for frames
        temp_dir = tempfile.mkdtemp(prefix='p61_frames_')
        frame_paths = []
        
        for i, timestamp in enumerate(timestamps):
            frame_filename = f'frame_{i+1}_{timestamp}s.jpg'
            frame_path = os.path.join(temp_dir, frame_filename)
            frame_paths.append(frame_path)
            
            print(f"   Extracting frame {i+1} at {timestamp}s...")
            
            # Use ffmpeg to extract frame at specific timestamp
            ffmpeg_cmd = [
                '/usr/local/bin/ffmpeg',
                '-ss', str(timestamp),  # Seek to timestamp
                '-i', video_url,        # Input video URL
                '-vframes', '1',        # Extract 1 frame
                '-q:v', '2',           # High quality
                '-vf', 'scale=160:90', # Resize to thumbnail size
                '-y',                  # Overwrite if exists
                frame_path
            ]
            
            try:
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and os.path.exists(frame_path):
                    size = os.path.getsize(frame_path)
                    print(f"      ✅ Extracted: {frame_filename} ({size:,} bytes)")
                else:
                    print(f"      ❌ Failed: {result.stderr}")
                    # Create placeholder
                    create_placeholder_frame(frame_path, f"{timestamp}s", "FAILED")
                    
            except subprocess.TimeoutExpired:
                print(f"      ⚠️ Timeout extracting frame at {timestamp}s")
                create_placeholder_frame(frame_path, f"{timestamp}s", "TIMEOUT")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                create_placeholder_frame(frame_path, f"{timestamp}s", "ERROR")
        
        print(f"\n🔧 Step 3: Creating sprite sheet...")
        
        # Combine frames into sprite sheet
        frame_width, frame_height = 160, 90
        frame_count = len(timestamps)
        sprite_width = frame_width * frame_count
        sprite_height = frame_height
        
        sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
        
        for i, frame_path in enumerate(frame_paths):
            try:
                if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                    frame_image = Image.open(frame_path)
                    frame_image = frame_image.resize((frame_width, frame_height))
                    
                    # Add timestamp overlay
                    add_timestamp_overlay(frame_image, f"{timestamps[i]}s")
                    
                    # Paste into sprite sheet
                    x_offset = i * frame_width
                    sprite_image.paste(frame_image, (x_offset, 0))
                    frame_image.close()
                    
                    print(f"   ✅ Added frame {i+1} to sprite")
                else:
                    print(f"   ⚠️ Frame {i+1} missing or empty, using placeholder")
                    create_placeholder_frame_in_sprite(sprite_image, i, frame_width, frame_height, f"{timestamps[i]}s")
                    
            except Exception as e:
                print(f"   ❌ Error processing frame {i+1}: {e}")
                create_placeholder_frame_in_sprite(sprite_image, i, frame_width, frame_height, f"{timestamps[i]}s")
        
        # Save sprite sheet
        sprite_path = os.path.join('/home/viblio/family_films/static/thumbnails/previews', f'{film.file_id}_sprite_real.jpg')
        sprite_image.save(sprite_path, 'JPEG', quality=90)
        sprite_image.close()
        
        print(f"\n✅ Real frame sprite created!")
        print(f"   Path: {sprite_path}")
        print(f"   Size: {os.path.getsize(sprite_path):,} bytes")
        
        # Save individual frames for inspection
        inspection_dir = '/home/viblio/family_films/debugging/frames_p61_real'
        os.makedirs(inspection_dir, exist_ok=True)
        
        for i, frame_path in enumerate(frame_paths):
            if os.path.exists(frame_path):
                import shutil
                dest_path = os.path.join(inspection_dir, f'real_frame_{i+1}_{timestamps[i]}s.jpg')
                shutil.copy2(frame_path, dest_path)
        
        print(f"📁 Individual frames saved to: {inspection_dir}")
        
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir)
        
        print(f"\n🧪 TESTING:")
        print(f"1. Compare new sprite: {sprite_path}")
        print(f"2. Check individual frames in: {inspection_dir}")
        print(f"3. Verify frames actually correspond to chapter content")
        print(f"4. If satisfied, replace the existing sprite file")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error extracting real frames: {e}")
        return False

def add_timestamp_overlay(image, timestamp_text):
    """Add timestamp overlay to image"""
    try:
        draw = ImageDraw.Draw(image)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # Add background and text
        text_bbox = draw.textbbox((0, 0), timestamp_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x, y = 4, 4
        draw.rectangle([x-2, y-2, x+text_width+2, y+text_height+2], fill=(0, 0, 0, 200))
        draw.text((x, y), timestamp_text, fill=(255, 255, 0), font=font)
        
    except Exception as e:
        print(f"Warning: Could not add timestamp overlay: {e}")

def create_placeholder_frame(frame_path, timestamp_text, status):
    """Create a placeholder frame when extraction fails"""
    try:
        placeholder = Image.new('RGB', (160, 90), (128, 128, 128))
        draw = ImageDraw.Draw(placeholder)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Draw timestamp and status
        draw.text((10, 30), timestamp_text, fill=(255, 255, 255), font=font)
        draw.text((10, 50), status, fill=(255, 0, 0), font=font)
        
        placeholder.save(frame_path, 'JPEG')
        placeholder.close()
    except Exception:
        pass

def create_placeholder_frame_in_sprite(sprite_image, frame_index, frame_width, frame_height, timestamp_text):
    """Create placeholder frame directly in sprite"""
    try:
        placeholder = Image.new('RGB', (frame_width, frame_height), (64, 64, 64))
        draw = ImageDraw.Draw(placeholder)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 30), timestamp_text, fill=(255, 255, 255), font=font)
        draw.text((10, 50), "NO FRAME", fill=(255, 0, 0), font=font)
        
        x_offset = frame_index * frame_width
        sprite_image.paste(placeholder, (x_offset, 0))
        placeholder.close()
    except Exception:
        pass

if __name__ == '__main__':
    extract_real_frames_p61()