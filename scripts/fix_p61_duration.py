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

def get_youtube_duration(youtube_id):
    """Get duration from YouTube using web scraping method"""
    try:
        # Method 1: Try to get duration from YouTube page HTML
        url = f"https://www.youtube.com/watch?v={youtube_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Look for duration in the HTML
        # YouTube embeds duration in various formats, try multiple patterns
        patterns = [
            r'"lengthSeconds":"(\d+)"',
            r'"approxDurationMs":"(\d+)"',
            r'videoDuration":{"simpleText":"([^"]+)"',
            r'"lengthText":{"simpleText":"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                duration_str = match.group(1)
                print(f"Found duration pattern: {pattern} -> {duration_str}")
                
                if duration_str.isdigit():
                    # Duration in seconds
                    seconds = int(duration_str)
                    if duration_str.endswith('000') and len(duration_str) > 3:
                        # Might be milliseconds
                        seconds = int(duration_str) // 1000
                    return timedelta(seconds=seconds)
                else:
                    # Duration in HH:MM:SS or MM:SS format
                    return parse_duration_string(duration_str)
        
        # Method 2: Look for schema.org microdata
        schema_pattern = r'"duration":"PT(\d+)M(\d+)S"'
        match = re.search(schema_pattern, response.text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            total_seconds = minutes * 60 + seconds
            print(f"Found schema duration: {minutes}m {seconds}s = {total_seconds}s")
            return timedelta(seconds=total_seconds)
        
        # Method 3: Look for ISO 8601 duration
        iso_pattern = r'"duration":"PT(\d+H)?(\d+M)?(\d+S)?"'
        match = re.search(iso_pattern, response.text)
        if match:
            hours = int(match.group(1)[:-1]) if match.group(1) else 0
            minutes = int(match.group(2)[:-1]) if match.group(2) else 0
            seconds = int(match.group(3)[:-1]) if match.group(3) else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            print(f"Found ISO duration: {hours}h {minutes}m {seconds}s = {total_seconds}s")
            return timedelta(seconds=total_seconds)
        
        print("No duration pattern found in YouTube page")
        return None
        
    except Exception as e:
        print(f"Error fetching from YouTube: {e}")
        return None

def parse_duration_string(duration_str):
    """Parse duration string like '12:34' or '1:23:45'"""
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return timedelta(minutes=minutes, seconds=seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except:
        pass
    return None

def manual_duration_check():
    """Manual method - ask user to check YouTube manually"""
    print("\n🔍 MANUAL DURATION CHECK")
    print("-" * 50)
    print("Please visit: https://www.youtube.com/watch?v=brPYVHx8rhw")
    print("Look at the video duration shown on the player")
    print("Enter the duration you see (format: MM:SS or HH:MM:SS)")
    
    duration_input = input("Duration: ").strip()
    
    if duration_input:
        duration = parse_duration_string(duration_input)
        if duration:
            return duration
        else:
            print("Invalid format. Please use MM:SS or HH:MM:SS")
    
    return None

def estimate_from_chapters():
    """Estimate duration based on last chapter timestamp"""
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        chapters = film.chapters.all().order_by('-start_time_seconds')
        if chapters.exists():
            last_chapter_time = chapters.first().start_time_seconds
            # Add some buffer (assume last chapter is about 2-3 minutes)
            estimated_duration = last_chapter_time + 180  # Add 3 minutes
            print(f"Last chapter at {last_chapter_time}s, estimating total: {estimated_duration}s")
            return timedelta(seconds=estimated_duration)
    except:
        pass
    return None

def fix_p61_duration():
    """Fix the missing duration for P-61_FROS"""
    
    print("=== Fixing P-61_FROS Duration ===\n")
    
    try:
        film = Film.objects.get(file_id='P-61_FROS')
        print(f"Current duration: {film.duration}")
        print(f"YouTube ID: {film.youtube_id}")
        print(f"YouTube URL: https://www.youtube.com/watch?v={film.youtube_id}")
        
        # Try to get duration from YouTube
        print(f"\n📡 Attempting to fetch duration from YouTube...")
        duration = get_youtube_duration(film.youtube_id)
        
        if not duration:
            print(f"Automatic fetch failed. Trying estimation from chapters...")
            duration = estimate_from_chapters()
        
        if not duration:
            print(f"Estimation failed. Requesting manual input...")
            duration = manual_duration_check()
        
        if duration:
            print(f"\n✅ Found duration: {duration}")
            print(f"   Total seconds: {int(duration.total_seconds())}")
            
            # Update the database
            film.duration = duration
            film.save()
            
            print(f"✅ Updated database with duration: {duration}")
            
            # Verify the update
            film.refresh_from_db()
            print(f"✅ Verified - Current duration in DB: {film.duration}")
            
        else:
            print(f"❌ Could not determine duration")
            print(f"💡 You can manually set it using:")
            print(f"   film = Film.objects.get(file_id='P-61_FROS')")
            print(f"   film.duration = timedelta(minutes=XX, seconds=XX)")
            print(f"   film.save()")
        
    except Film.DoesNotExist:
        print("❌ Film P-61_FROS not found")

if __name__ == '__main__':
    fix_p61_duration()