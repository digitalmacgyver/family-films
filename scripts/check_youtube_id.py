#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

youtube_id = 'YFIDOmMvxiY'
youtube_url = f'https://www.youtube.com/watch?v={youtube_id}'

print(f'=== CHECKING FILE IDs FOR YOUTUBE VIDEO {youtube_id} ===\n')

# Find films with this YouTube ID
films = Film.objects.filter(youtube_id=youtube_id)

if films.exists():
    print(f'Films associated with {youtube_url}:\n')
    for film in films:
        print(f'* File ID: {film.file_id}')
        print(f'  Title: {film.title}')
        print(f'  Years: {film.years}')
        print(f'  Description: {film.description[:200]}...')
        print()
else:
    print(f'No films found with YouTube ID: {youtube_id}')

# Also show what this video is in our YouTube data
try:
    with open('youtube_videos.json', 'r') as f:
        videos = json.load(f)
    
    for video in videos:
        if video['video_id'] == youtube_id:
            print(f'\nYouTube video information:')
            print(f'  Video ID: {video["video_id"]}')
            print(f'  Title: {video["title"]}')
            print(f'  URL: {video["url"]}')
            break
except:
    pass