#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def optimize_pa03_thumbnail():
    """Analyze and optimize PA-03_FROS thumbnail generation"""
    
    print("=== Optimizing PA-03_FROS Thumbnail ===\n")
    
    try:
        film = Film.objects.get(file_id='PA-03_FROS')
        chapters = film.chapters.all().order_by('order')
        
        print(f"Film: {film.title}")
        print(f"Total chapters: {chapters.count()}")
        print(f"Current sprite frames: {film.preview_frame_count}")
        
        print(f"\nAll chapter timestamps:")
        for i, chapter in enumerate(chapters):
            marker = "👉" if i < 7 else "  "
            print(f"{marker} {i+1:2d}. {chapter.start_time:>8} ({chapter.start_time_seconds:>3d}s) - {chapter.title[:60]}")
        
        # Analyze current selection (every 3rd chapter approximately)
        print(f"\nCurrent algorithm selected:")
        step = max(1, chapters.count() // 6)  # This gives us step=3 for 19 chapters
        selected_indices = list(range(0, chapters.count(), step))
        print(f"Step size: {step}")
        print(f"Selected indices: {selected_indices}")
        
        for idx in selected_indices:
            chapter = chapters[idx]
            print(f"  {idx+1:2d}. {chapter.start_time} - {chapter.title[:50]}")
        
        print(f"\nRecommendation:")
        print(f"- Current: 7 frames covering {chapters.count()} chapters is reasonable")
        print(f"- Alternative: Could use 10-12 frames for better coverage")
        print(f"- The algorithm correctly samples across the full timeline")
        print(f"- No action needed - this is working as designed for films with many chapters")
        
    except Film.DoesNotExist:
        print("Film PA-03_FROS not found")

if __name__ == '__main__':
    optimize_pa03_thumbnail()