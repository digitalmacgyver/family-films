#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter

def verify_chapter_functionality():
    """Verify that chapters have the necessary data for click-to-play functionality"""
    
    print("=== Verifying Chapter Click-to-Play Functionality ===\n")
    
    # Get a film with chapters
    film = Film.objects.filter(chapters__isnull=False).first()
    
    if not film:
        print("❌ No films with chapters found!")
        return False
    
    print(f"✓ Testing film: {film.title} ({film.file_id})")
    print(f"✓ YouTube ID: {film.youtube_id}")
    print(f"✓ YouTube URL: {film.get_youtube_embed_url()}")
    print()
    
    chapters = film.chapters.all().order_by('order')
    print(f"✓ Found {chapters.count()} chapters:")
    
    all_good = True
    
    for chapter in chapters:
        print(f"  - Chapter {chapter.order}: {chapter.title}")
        print(f"    Start time: {chapter.start_time} ({chapter.start_time_seconds} seconds)")
        
        # Check if start_time_seconds is valid
        if chapter.start_time_seconds is None or chapter.start_time_seconds < 0:
            print(f"    ❌ Invalid start_time_seconds: {chapter.start_time_seconds}")
            all_good = False
        else:
            print(f"    ✓ Valid start_time_seconds: {chapter.start_time_seconds}")
        
        # Check if chapter has thumbnail
        thumbnail_url = chapter.get_thumbnail_url()
        print(f"    Thumbnail: {thumbnail_url}")
        print()
    
    if all_good:
        print("✅ All chapter data looks good for click-to-play functionality!")
        print("\nTo test manually:")
        print(f"1. Visit: http://localhost:8000/films/{film.file_id}/")
        print("2. Click on any chapter in the right sidebar")
        print("3. The YouTube video should seek to that chapter's timestamp")
        print("4. Check browser console for debug messages")
    else:
        print("❌ Some issues found with chapter data")
    
    return all_good

if __name__ == '__main__':
    verify_chapter_functionality()