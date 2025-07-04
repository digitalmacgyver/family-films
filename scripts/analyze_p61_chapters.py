#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter

def analyze_p61_chapters():
    """Analyze chapters for P-61_FROS test video"""
    
    print("=== Analyzing P-61_FROS Test Video ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        print(f"🎬 FILM DETAILS:")
        print(f"   Title: {film.title}")
        print(f"   File ID: {film.file_id}")
        print(f"   YouTube ID: {film.youtube_id}")
        print(f"   YouTube URL: https://www.youtube.com/watch?v={film.youtube_id}")
        print(f"   Duration: {film.duration}")
        
        chapters = film.chapters.all().order_by('order')
        print(f"\n📋 CHAPTERS ({chapters.count()} total):")
        print(f"{'#':<3} {'Start Time':<10} {'Seconds':<8} {'Title'}")
        print("-" * 80)
        
        for i, chapter in enumerate(chapters, 1):
            print(f"{i:<3} {chapter.start_time:<10} {chapter.start_time_seconds:<8} {chapter.title}")
        
        print(f"\n🖼️ CURRENT THUMBNAIL INFO:")
        print(f"   Sprite URL: {film.preview_sprite_url}")
        print(f"   Frame count: {film.preview_frame_count}")
        print(f"   Frame interval: {film.preview_frame_interval}")
        print(f"   Frame size: {film.preview_sprite_width}x{film.preview_sprite_height}")
        
        # Check if sprite file exists
        if film.preview_sprite_url:
            sprite_path = film.preview_sprite_url.lstrip('/')
            full_path = os.path.join('/home/viblio/family_films', sprite_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"   ✅ Sprite file exists: {size:,} bytes")
            else:
                print(f"   ❌ Sprite file missing: {full_path}")
        
        print(f"\n⏱️ TIMESTAMP ANALYSIS:")
        duration_seconds = int(film.duration.total_seconds()) if film.duration else None
        if duration_seconds:
            print(f"   Total video duration: {duration_seconds} seconds ({film.duration})")
            
            if chapters.exists():
                last_chapter_start = chapters.last().start_time_seconds
                print(f"   Last chapter starts at: {last_chapter_start} seconds")
                print(f"   Coverage: {last_chapter_start/duration_seconds*100:.1f}% of video")
                
                # Show time gaps between chapters
                print(f"\n   Chapter gaps:")
                prev_time = 0
                for chapter in chapters:
                    gap = chapter.start_time_seconds - prev_time
                    print(f"     Gap before '{chapter.title}': {gap} seconds")
                    prev_time = chapter.start_time_seconds
                
                # Show what timestamps we should extract frames at
                print(f"\n📸 RECOMMENDED FRAME EXTRACTION TIMES:")
                for i, chapter in enumerate(chapters):
                    print(f"   Frame {i+1}: {chapter.start_time_seconds}s - {chapter.title}")
        
        print(f"\n🎯 TEST PLAN:")
        print(f"1. Verify these chapter timestamps are correct")
        print(f"2. Generate sprite with frames at these exact times")
        print(f"3. Test animated thumbnail on film card")
        print(f"4. Verify individual chapter thumbnails if needed")
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")

if __name__ == '__main__':
    analyze_p61_chapters()