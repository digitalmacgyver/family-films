#!/usr/bin/env python
import os
import sys
import django
import subprocess
import json
import re

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def get_playlist_order():
    """Fetch playlist order from YouTube using yt-dlp"""
    playlist_url = "https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm"
    
    try:
        cmd = [
            os.path.expanduser('~/.local/bin/yt-dlp'),
            '--flat-playlist',
            '--dump-json',
            '--no-warnings',
            playlist_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        playlist_order = {}
        order_index = 1
        
        # Process each line (each video is a separate JSON object)
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    entry = json.loads(line)
                    video_id = entry.get('id')
                    title = entry.get('title', '')
                    
                    if video_id:
                        playlist_order[video_id] = {
                            'order': order_index,
                            'title': title
                        }
                        order_index += 1
                        
                except json.JSONDecodeError:
                    continue
        
        return playlist_order
        
    except subprocess.CalledProcessError as e:
        print(f"Error fetching playlist: {e}")
        return {}

def update_film_playlist_order():
    """Update films with their playlist order"""
    print("Fetching YouTube playlist order...")
    playlist_order = get_playlist_order()
    
    if not playlist_order:
        print("Failed to fetch playlist order")
        return
    
    print(f"Found {len(playlist_order)} videos in playlist")
    
    updated_count = 0
    not_found_count = 0
    
    # Update each film with its playlist order
    for youtube_id, data in playlist_order.items():
        try:
            film = Film.objects.get(youtube_id=youtube_id)
            
            # Check if we need to add a playlist_order field to the model
            if not hasattr(film, 'playlist_order'):
                print("Need to add playlist_order field to Film model")
                break
                
            film.playlist_order = data['order']
            film.save()
            
            updated_count += 1
            print(f"Updated {film.file_id} (order {data['order']})")
            
        except Film.DoesNotExist:
            not_found_count += 1
            print(f"YouTube video {youtube_id} not found in database: {data['title'][:50]}...")
    
    print(f"\nSummary:")
    print(f"Updated: {updated_count}")
    print(f"Not found in DB: {not_found_count}")

if __name__ == '__main__':
    update_film_playlist_order()