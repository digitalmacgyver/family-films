#!/usr/bin/env python3

import django
import os
import sys
import requests
import re
import tempfile
import json
from urllib.parse import parse_qs, urlparse

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film
from PIL import Image, ImageDraw, ImageFont

def extract_storyboard_data(video_id):
    """Extract storyboard data from YouTube page"""
    
    print(f"🔍 Extracting storyboard data for video: {video_id}")
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.text
        
        # Look for storyboard data in the page
        storyboard_pattern = r'"playerStoryboardSpecRenderer":\s*{"spec":"([^"]+)"'
        match = re.search(storyboard_pattern, content)
        
        if match:
            storyboard_url_template = match.group(1)
            print(f"✅ Found storyboard template: {storyboard_url_template[:100]}...")
            
            # Parse the template to understand the format
            # Template usually looks like: https://i.ytimg.com/sb/VIDEO_ID/storyboard3_L$L/$N.jpg?sqp=...
            
            # Extract parameters from the URL
            if 'storyboard3_L' in storyboard_url_template:
                # This is a level-based storyboard
                return parse_level_storyboard(storyboard_url_template, video_id)
            else:
                print(f"⚠️ Unknown storyboard format")
                return None
        else:
            print(f"❌ No storyboard data found")
            return None
            
    except Exception as e:
        print(f"❌ Error extracting storyboard data: {e}")
        return None

def parse_level_storyboard(template_url, video_id):
    """Parse level-based storyboard template"""
    
    print(f"📋 Parsing level storyboard template...")
    
    # Try different levels to find available storyboards
    storyboard_info = {
        'template': template_url,
        'available_levels': []
    }
    
    for level in range(0, 5):  # Try levels 0-4
        # Replace $L with level number
        test_url = template_url.replace('$L', str(level)).replace('$N', '0')
        
        try:
            response = requests.head(test_url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Level {level} available: {response.headers.get('content-length', 'unknown')} bytes")
                storyboard_info['available_levels'].append(level)
            else:
                print(f"   ❌ Level {level}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Level {level}: {e}")
    
    if storyboard_info['available_levels']:
        # Use the highest available level for best quality
        best_level = max(storyboard_info['available_levels'])
        storyboard_info['best_level'] = best_level
        print(f"📊 Using level {best_level} for extraction")
        return storyboard_info
    else:
        print(f"❌ No storyboard levels available")
        return None

def download_storyboard_images(storyboard_info, video_id):
    """Download storyboard images for analysis"""
    
    if not storyboard_info or 'best_level' not in storyboard_info:
        return None
    
    level = storyboard_info['best_level']
    template = storyboard_info['template']
    
    print(f"📥 Downloading storyboard images for level {level}...")
    
    # Try to download first few storyboard images
    downloaded_images = []
    
    for n in range(0, 10):  # Try first 10 images
        image_url = template.replace('$L', str(level)).replace('$N', str(n))
        
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix=f'_sb_{n}.jpg', delete=False)
                temp_file.write(response.content)
                temp_file.close()
                
                downloaded_images.append({
                    'index': n,
                    'path': temp_file.name,
                    'size': len(response.content)
                })
                
                print(f"   ✅ Downloaded image {n}: {len(response.content):,} bytes")
            else:
                print(f"   ❌ Image {n}: HTTP {response.status_code}")
                break  # Stop when we hit a missing image
                
        except Exception as e:
            print(f"   ❌ Image {n}: {e}")
            break
    
    print(f"📊 Downloaded {len(downloaded_images)} storyboard images")
    return downloaded_images

def analyze_storyboard_structure(downloaded_images):
    """Analyze the structure of downloaded storyboard images"""
    
    if not downloaded_images:
        return None
    
    print(f"🔍 Analyzing storyboard structure...")
    
    # Analyze the first image to understand the grid structure
    first_image_path = downloaded_images[0]['path']
    
    try:
        with Image.open(first_image_path) as img:
            width, height = img.size
            print(f"   Storyboard image size: {width}x{height}")
            
            # Common storyboard formats:
            # - 10x10 grid = 100 frames per image
            # - 5x5 grid = 25 frames per image
            # - 4x4 grid = 16 frames per image
            
            possible_grids = [
                (10, 10, 100),  # cols, rows, total_frames
                (5, 5, 25),
                (4, 4, 16),
                (8, 6, 48),
                (6, 5, 30)
            ]
            
            for cols, rows, total_frames in possible_grids:
                frame_width = width // cols
                frame_height = height // rows
                
                if frame_width > 50 and frame_height > 30:  # Reasonable frame size
                    print(f"   Possible grid: {cols}x{rows} = {total_frames} frames")
                    print(f"   Frame size: {frame_width}x{frame_height}")
                    
                    return {
                        'image_width': width,
                        'image_height': height,
                        'grid_cols': cols,
                        'grid_rows': rows,
                        'frames_per_image': total_frames,
                        'frame_width': frame_width,
                        'frame_height': frame_height,
                        'images': downloaded_images
                    }
            
            print(f"   ⚠️ Could not determine grid structure")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing storyboard: {e}")
        return None

def extract_frames_from_storyboard(storyboard_data, target_timestamps, video_duration_seconds):
    """Extract specific frames from storyboard images"""
    
    if not storyboard_data:
        return []
    
    print(f"🎯 Extracting frames for timestamps: {target_timestamps}")
    
    frames_per_image = storyboard_data['frames_per_image']
    total_images = len(storyboard_data['images'])
    total_frames_available = frames_per_image * total_images
    
    # Calculate time per frame
    time_per_frame = video_duration_seconds / total_frames_available
    
    print(f"   Video duration: {video_duration_seconds}s")
    print(f"   Total frames: {total_frames_available}")
    print(f"   Time per frame: {time_per_frame:.2f}s")
    
    extracted_frames = []
    
    for target_time in target_timestamps:
        # Calculate which frame index corresponds to this timestamp
        frame_index = int(target_time / time_per_frame)
        
        # Calculate which storyboard image contains this frame
        image_index = frame_index // frames_per_image
        frame_in_image = frame_index % frames_per_image
        
        if image_index >= len(storyboard_data['images']):
            print(f"   ⚠️ Timestamp {target_time}s beyond available frames")
            continue
        
        # Calculate grid position
        cols = storyboard_data['grid_cols']
        col = frame_in_image % cols
        row = frame_in_image // cols
        
        print(f"   Timestamp {target_time}s → frame {frame_index} → image {image_index}, grid ({col}, {row})")
        
        try:
            # Extract the specific frame from the storyboard
            storyboard_path = storyboard_data['images'][image_index]['path']
            
            with Image.open(storyboard_path) as storyboard:
                frame_width = storyboard_data['frame_width']
                frame_height = storyboard_data['frame_height']
                
                x = col * frame_width
                y = row * frame_height
                
                frame_box = (x, y, x + frame_width, y + frame_height)
                frame = storyboard.crop(frame_box)
                
                # Resize to standard thumbnail size
                frame = frame.resize((160, 90))
                
                extracted_frames.append({
                    'timestamp': target_time,
                    'image': frame.copy()
                })
                
                print(f"      ✅ Extracted frame for {target_time}s")
        
        except Exception as e:
            print(f"      ❌ Error extracting frame for {target_time}s: {e}")
    
    return extracted_frames

def create_sprite_from_storyboard():
    """Create sprite from storyboard data for P-61_FROS"""
    
    print("=== Creating Sprite from YouTube Storyboard ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"🎬 Film: {film.title}")
        print(f"📺 YouTube ID: {film.youtube_id}")
        print(f"⏱️ Duration: {film.duration} ({int(film.duration.total_seconds())}s)")
        
        target_timestamps = [ch.start_time_seconds for ch in chapters]
        print(f"🎯 Target timestamps: {target_timestamps}")
        
        # Extract storyboard data
        storyboard_info = extract_storyboard_data(film.youtube_id)
        if not storyboard_info:
            print("❌ Could not get storyboard data")
            return False
        
        # Download storyboard images
        downloaded_images = download_storyboard_images(storyboard_info, film.youtube_id)
        if not downloaded_images:
            print("❌ Could not download storyboard images")
            return False
        
        # Analyze structure
        storyboard_data = analyze_storyboard_structure(downloaded_images)
        if not storyboard_data:
            print("❌ Could not analyze storyboard structure")
            return False
        
        # Extract frames
        extracted_frames = extract_frames_from_storyboard(
            storyboard_data, 
            target_timestamps, 
            int(film.duration.total_seconds())
        )
        
        if not extracted_frames:
            print("❌ Could not extract any frames")
            return False
        
        print(f"\n🔧 Creating sprite from {len(extracted_frames)} extracted frames...")
        
        # Create sprite sheet
        frame_width, frame_height = 160, 90
        sprite_width = frame_width * len(extracted_frames)
        sprite_height = frame_height
        
        sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
        
        for i, frame_data in enumerate(extracted_frames):
            frame = frame_data['image']
            timestamp = frame_data['timestamp']
            
            # Add timestamp overlay
            draw = ImageDraw.Draw(frame)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            timestamp_text = f"{timestamp}s"
            text_bbox = draw.textbbox((0, 0), timestamp_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x, y = 4, 4
            draw.rectangle([x-2, y-2, x+text_width+2, y+text_height+2], fill=(0, 0, 0, 180))
            draw.text((x, y), timestamp_text, fill=(255, 255, 0), font=font)
            
            # Paste into sprite
            x_offset = i * frame_width
            sprite_image.paste(frame, (x_offset, 0))
        
        # Save sprite
        sprite_path = os.path.join('/home/viblio/family_films/static/thumbnails/previews', f'{film.file_id}_sprite_storyboard.jpg')
        sprite_image.save(sprite_path, 'JPEG', quality=90)
        sprite_image.close()
        
        print(f"✅ Storyboard sprite created!")
        print(f"   Path: {sprite_path}")
        print(f"   Size: {os.path.getsize(sprite_path):,} bytes")
        
        # Cleanup downloaded images
        for img_data in downloaded_images:
            try:
                os.unlink(img_data['path'])
            except:
                pass
        
        print(f"\n🧪 TESTING:")
        print(f"Compare this sprite with the previous one to see if frames are more accurate")
        print(f"Sprite location: {sprite_path}")
        
        return True
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False
    except Exception as e:
        print(f"❌ Error creating storyboard sprite: {e}")
        return False

if __name__ == '__main__':
    create_sprite_from_storyboard()