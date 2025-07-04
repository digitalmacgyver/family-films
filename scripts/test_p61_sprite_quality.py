#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film
from PIL import Image

def test_p61_sprite_quality():
    """Test the current sprite file quality and content for P-61_FROS"""
    
    print("=== Testing P-61_FROS Current Sprite Quality ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        print(f"🎬 Film: {film.title}")
        print(f"📊 Sprite Info:")
        print(f"   URL: {film.preview_sprite_url}")
        print(f"   Frame count: {film.preview_frame_count}")
        print(f"   Frame size: {film.preview_sprite_width}x{film.preview_sprite_height}")
        print(f"   Frame interval: {film.preview_frame_interval}s")
        
        # Check if sprite file exists
        sprite_path = film.preview_sprite_url.lstrip('/')
        full_path = os.path.join('/home/viblio/family_films', sprite_path)
        
        if not os.path.exists(full_path):
            print(f"❌ Sprite file not found: {full_path}")
            return False
        
        file_size = os.path.getsize(full_path)
        print(f"   File size: {file_size:,} bytes")
        
        # Analyze the sprite image
        try:
            sprite_image = Image.open(full_path)
            width, height = sprite_image.size
            print(f"\n🖼️ Sprite Image Analysis:")
            print(f"   Total dimensions: {width}x{height}")
            print(f"   Expected: {film.preview_frame_count * film.preview_sprite_width}x{film.preview_sprite_height}")
            
            # Check if dimensions match expectations
            expected_width = film.preview_frame_count * film.preview_sprite_width
            expected_height = film.preview_sprite_height
            
            if width == expected_width and height == expected_height:
                print(f"   ✅ Dimensions match expectations")
            else:
                print(f"   ⚠️ Dimensions don't match (expected {expected_width}x{expected_height})")
            
            # Extract individual frames for visual inspection
            frame_width = film.preview_sprite_width
            frame_height = film.preview_sprite_height
            
            print(f"\n📸 Frame Analysis:")
            frames_dir = '/home/viblio/family_films/debugging/frames_p61'
            os.makedirs(frames_dir, exist_ok=True)
            
            for i in range(film.preview_frame_count):
                x_offset = i * frame_width
                frame_box = (x_offset, 0, x_offset + frame_width, frame_height)
                frame_image = sprite_image.crop(frame_box)
                
                frame_path = os.path.join(frames_dir, f'frame_{i+1}.jpg')
                frame_image.save(frame_path, 'JPEG', quality=90)
                frame_image.close()
                
                print(f"   Frame {i+1}: Extracted to {frame_path}")
            
            sprite_image.close()
            
            print(f"\n✅ Sprite analysis complete!")
            print(f"📁 Individual frames saved to: {frames_dir}")
            print(f"💡 You can visually inspect these frames to see if they represent the correct timestamps")
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing sprite image: {e}")
            return False
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")
        return False

def test_animation_template():
    """Test if the animation template code is working"""
    
    print(f"\n=== Testing Animation Template Integration ===\n")
    
    # Check if the animated thumbnail template exists and has the right code
    template_paths = [
        '/home/viblio/family_films/films/templates/films/catalog.html',
        '/home/viblio/family_films/films/templates/films/base.html',
        '/home/viblio/family_films/search/templates/search/overall.html'
    ]
    
    for template_path in template_paths:
        if os.path.exists(template_path):
            print(f"📄 Checking {os.path.basename(template_path)}:")
            
            with open(template_path, 'r') as f:
                content = f.read()
                
            # Check for animated thumbnail code
            checks = [
                ('has_animated_thumbnail', 'has_animated_thumbnail' in content),
                ('animated-thumbnail class', 'animated-thumbnail' in content),
                ('data-sprite-url', 'data-sprite-url' in content),
                ('data-frame-count', 'data-frame-count' in content),
                ('preview_sprite_url', 'preview_sprite_url' in content)
            ]
            
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
            
            print()
    
    # Check for JavaScript animation code
    print(f"🔍 Looking for animation JavaScript...")
    
    static_js_dir = '/home/viblio/family_films/static/js'
    if os.path.exists(static_js_dir):
        js_files = [f for f in os.listdir(static_js_dir) if f.endswith('.js')]
        print(f"   Found JS files: {js_files}")
        
        for js_file in js_files:
            js_path = os.path.join(static_js_dir, js_file)
            with open(js_path, 'r') as f:
                js_content = f.read()
            
            if 'animated-thumbnail' in js_content or 'sprite' in js_content.lower():
                print(f"   ✅ {js_file} contains animation code")
            else:
                print(f"   ➖ {js_file} no animation code")
    
    print(f"\n💡 Next: Check the film catalog page to see if P-61_FROS shows animated thumbnails")

if __name__ == '__main__':
    success = test_p61_sprite_quality()
    if success:
        test_animation_template()
    else:
        print("⚠️ Sprite analysis failed - need to regenerate sprite first")