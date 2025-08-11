#!/usr/bin/env python3
"""
Fix 75-SLD_FROS Chapter Information

Update chapter timings based on YouTube video description and replace
first chapter thumbnail with film thumbnail.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film, Chapter
from django.db import transaction

def fix_75_sld_fros_chapters():
    """Fix chapter timings and thumbnails for 75-SLD_FROS"""
    print("=== FIXING 75-SLD_FROS CHAPTER INFORMATION ===")
    
    try:
        film = Film.objects.get(file_id='75-SLD_FROS')
        print(f"Found film: {film.title}")
        print(f"YouTube ID: {film.youtube_id}")
        
        # Correct chapter information from YouTube description
        correct_chapters = [
            {"start_time": "00:01", "title": "Baby Jonathan in bath with Linda"},
            {"start_time": "00:09", "title": "Baby Jonathan's Crib and Bedroom"},
            {"start_time": "00:37", "title": "Baby Jonathan in Bath with John"},
            {"start_time": "00:46", "title": "Zoo Visit with Linda and Jonathan"},
        ]
        
        # Get current chapters
        current_chapters = list(film.chapters.all().order_by('order'))
        print(f"\nCurrent chapters: {len(current_chapters)}")
        for i, ch in enumerate(current_chapters):
            print(f"  {i+1}. {ch.start_time} - {ch.title}")
        
        print(f"\nCorrect chapters from YouTube:")
        for i, ch_data in enumerate(correct_chapters):
            print(f"  {i+1}. {ch_data['start_time']} - {ch_data['title']}")
        
        # Update chapters with correct timings
        with transaction.atomic():
            for i, ch_data in enumerate(correct_chapters):
                if i < len(current_chapters):
                    chapter = current_chapters[i]
                    old_start_time = chapter.start_time
                    old_title = chapter.title
                    
                    # Update timing and title
                    chapter.start_time = ch_data['start_time']
                    chapter.title = ch_data['title']
                    chapter.save()
                    
                    print(f"\n✓ Updated Chapter {i+1}:")
                    print(f"    Start time: {old_start_time} → {ch_data['start_time']}")
                    print(f"    Title: {old_title} → {ch_data['title']}")
                else:
                    print(f"⚠️ Missing chapter {i+1} in database")
        
        # Replace first chapter thumbnail with film thumbnail
        if current_chapters:
            first_chapter = current_chapters[0]
            film_thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/maxresdefault.jpg"
            
            old_thumbnail = first_chapter.thumbnail_url
            first_chapter.thumbnail_url = film_thumbnail_url
            first_chapter.save()
            
            print(f"\n✓ Updated first chapter thumbnail:")
            print(f"    Old: {old_thumbnail}")
            print(f"    New: {film_thumbnail_url}")
        
        print(f"\n✅ Successfully updated 75-SLD_FROS chapters!")
        
        # Verify updates
        updated_chapters = list(film.chapters.all().order_by('order'))
        print(f"\nVerification - Updated chapters:")
        for i, ch in enumerate(updated_chapters):
            print(f"  {i+1}. {ch.start_time} - {ch.title}")
            print(f"      Thumbnail: {ch.thumbnail_url}")
        
    except Film.DoesNotExist:
        print("❌ Film 75-SLD_FROS not found in database")
    except Exception as e:
        print(f"❌ Error updating chapters: {e}")

def main():
    fix_75_sld_fros_chapters()
    return 0

if __name__ == "__main__":
    sys.exit(main())