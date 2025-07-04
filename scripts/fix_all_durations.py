#!/usr/bin/env python3

import django
import os
import sys
import requests
import re
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film

def get_youtube_duration(video_id):
    """Get video duration from YouTube using the same method as fix_p61_duration.py"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Look for duration in the page content
        duration_pattern = r'"lengthSeconds":"(\d+)"'
        match = re.search(duration_pattern, response.text)
        
        if match:
            seconds = int(match.group(1))
            duration = timedelta(seconds=seconds)
            print(f"  ✅ Found duration: {duration} ({seconds}s)")
            return duration
        else:
            print(f"  ❌ Could not find duration pattern")
            return None
            
    except Exception as e:
        print(f"  ❌ Error fetching duration: {e}")
        return None

def fix_all_durations():
    """Fix missing durations for all films"""
    
    print("=== Fixing Durations for All Films ===\n")
    
    # Get all films
    films = Film.objects.all().order_by('file_id')
    print(f"Found {films.count()} total films")
    
    # Check which films have missing or zero durations
    films_needing_fix = []
    
    for film in films:
        if not film.duration or film.duration.total_seconds() == 0:
            films_needing_fix.append(film)
    
    print(f"Found {len(films_needing_fix)} films with missing/zero durations:\n")
    
    for film in films_needing_fix:
        print(f"  {film.file_id}: {film.title[:50]}...")
    
    if not films_needing_fix:
        print("✅ All films already have durations!")
        return True
    
    print(f"\n🔧 Processing {len(films_needing_fix)} films...\n")
    
    fixed_count = 0
    failed_count = 0
    
    for i, film in enumerate(films_needing_fix, 1):
        print(f"[{i}/{len(films_needing_fix)}] Processing {film.file_id}: {film.title[:40]}...")
        
        if not film.youtube_id:
            print(f"  ⚠️ No YouTube ID, skipping")
            failed_count += 1
            continue
        
        # Get duration from YouTube
        duration = get_youtube_duration(film.youtube_id)
        
        if duration:
            # Update the film
            film.duration = duration
            film.save()
            print(f"  ✅ Updated duration to {duration}")
            fixed_count += 1
        else:
            print(f"  ❌ Failed to get duration")
            failed_count += 1
        
        print()
    
    print(f"=== Duration Fix Summary ===")
    print(f"✅ Fixed: {fixed_count} films")
    print(f"❌ Failed: {failed_count} films")
    print(f"📊 Total processed: {len(films_needing_fix)} films")
    
    return fixed_count > 0

if __name__ == '__main__':
    fix_all_durations()