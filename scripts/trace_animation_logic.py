#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def trace_animation_logic():
    """Trace the exact animation logic for P-61_FROS sprite"""
    
    print("=== Animation Logic Trace for P-61_FROS ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        
        # Get database values
        sprite_width = film.preview_sprite_width  # Individual frame width
        frame_count = film.preview_frame_count
        frame_interval = film.preview_frame_interval
        
        print(f"Database Values:")
        print(f"  sprite_width (per frame): {sprite_width}px")
        print(f"  frame_count: {frame_count}")
        print(f"  frame_interval: {frame_interval}s")
        print()
        
        # Check actual sprite dimensions
        sprite_path = os.path.join('/home/viblio/family_films', film.preview_sprite_url.lstrip('/'))
        from PIL import Image
        with Image.open(sprite_path) as img:
            total_width, total_height = img.size
            calculated_frame_width = total_width / frame_count
            
        print(f"Actual Sprite File:")
        print(f"  Total dimensions: {total_width}x{total_height}px")
        print(f"  Calculated frame width: {calculated_frame_width}px")
        print()
        
        # Simulate the JavaScript animation logic
        print("JavaScript Animation Logic Simulation:")
        print("  nextFrame() increments currentFrame from 0 to frameCount-1")
        print("  updateSpritePosition() calculates: pixelOffset = currentFrame * frameWidth")
        print("  CSS backgroundPosition = `-${pixelOffset}px 0`")
        print()
        
        print("Frame-by-Frame Animation:")
        for frame in range(frame_count):
            # This matches the JavaScript logic:
            # this.currentFrame = (this.currentFrame + 1) % this.frameCount;
            # const frameWidth = this.spriteWidth;
            # const pixelOffset = this.currentFrame * frameWidth;
            # this.spriteOverlay.style.backgroundPosition = `-${pixelOffset}px 0`;
            
            pixel_offset = frame * sprite_width
            
            print(f"  Frame {frame}:")
            print(f"    currentFrame = {frame}")
            print(f"    pixelOffset = {frame} × {sprite_width} = {pixel_offset}px")
            print(f"    backgroundPosition = '-{pixel_offset}px 0'")
            print(f"    Shows sprite region from {pixel_offset}px to {pixel_offset + sprite_width}px")
            print()
        
        # Visual representation of what should be shown
        print("Expected Visual Result:")
        chapters = film.chapters.all().order_by('order')
        for i, chapter in enumerate(chapters):
            pixel_start = i * sprite_width
            pixel_end = pixel_start + sprite_width
            print(f"  Frame {i}: Shows Chapter {i+1} ({chapter.start_time}) from pixels {pixel_start}-{pixel_end}")
        
        print()
        print("Potential Issues to Check:")
        print("1. Is the sprite actually being positioned at these pixel offsets?")
        print("2. Is CSS scaling affecting the positioning?")
        print("3. Are there any container size constraints?")
        print("4. Is the background-size property interfering?")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    trace_animation_logic()