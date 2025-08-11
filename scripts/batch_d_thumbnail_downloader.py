#!/usr/bin/env python3
"""
Batch D Thumbnail Downloader

This script finds the real YouTube videos for Batch D films by matching File IDs 
in video descriptions, downloads thumbnails, and updates film records.
"""

import os
import sys
import django
import subprocess
import json
import requests
from urllib.parse import urlparse
import time

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

class BatchDThumbnailDownloader:
    def __init__(self):
        self.youtube_playlist_url = 'https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm'
        self.thumbnails_dir = '/home/viblio/family_films/static/thumbnails'
        self.stats = {
            'processed': 0,
            'matched': 0,
            'downloaded': 0,
            'errors': 0
        }
        
    def fetch_youtube_video_with_description(self, video_id):
        """Fetch individual video details including description using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--skip-download',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"      ❌ yt-dlp failed for {video_id}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"      ❌ Timeout fetching video {video_id}")
            return None
        except Exception as e:
            print(f"      ❌ Error fetching video {video_id}: {e}")
            return None

    def find_youtube_video_by_file_id(self, file_id):
        """Find YouTube video by searching for File ID in descriptions"""
        print(f"    🔍 Searching for YouTube video with File ID: {file_id}")
        
        # Load existing video list as starting point
        youtube_json_file = '/home/viblio/family_films/scripts/youtube_videos.json'
        
        try:
            if os.path.exists(youtube_json_file):
                with open(youtube_json_file, 'r') as f:
                    videos = json.load(f)
                    
                # Search through videos and get their descriptions
                for video in videos:
                    video_id = video.get('video_id')
                    if not video_id:
                        continue
                        
                    print(f"      📄 Checking video: {video.get('title', 'Unknown')}")
                    video_details = self.fetch_youtube_video_with_description(video_id)
                    
                    if video_details:
                        description = video_details.get('description', '')
                        if f"File ID: {file_id}" in description:
                            print(f"      ✅ Found matching video: {video_details.get('title', 'Unknown')}")
                            return {
                                'youtube_id': video_id,
                                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                                'title': video_details.get('title', ''),
                                'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                                'thumbnail_hq_url': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                                'thumbnail_med_url': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                            }
                    
                    # Add small delay to be nice to YouTube
                    time.sleep(1)
                    
        except Exception as e:
            print(f"    ❌ Error searching videos: {e}")
        
        print(f"    ⚠️ No YouTube video found with File ID: {file_id}")
        return None

    def download_thumbnail(self, url, file_path):
        """Download thumbnail image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"        ❌ Error downloading {url}: {e}")
            return False

    def process_batch_d_films(self):
        """Process all Batch D films and update their thumbnails"""
        print("=== BATCH D THUMBNAIL DOWNLOADER ===\\n")
        
        # Get all Batch D films (placeholder YouTube IDs) - limit to 3 for testing
        batch_d_films = Film.objects.filter(youtube_id__startswith='placeholder_', file_id__contains='SLD').order_by('file_id')[:3]
        
        print(f"Found {batch_d_films.count()} Batch D films to process\\n")
        
        for film in batch_d_films:
            self.stats['processed'] += 1
            print(f"[{self.stats['processed']}/{batch_d_films.count()}] Processing: {film.file_id}")
            
            try:
                # Find the real YouTube video
                youtube_info = self.find_youtube_video_by_file_id(film.file_id)
                
                if youtube_info:
                    self.stats['matched'] += 1
                    
                    # Download thumbnail images
                    thumbnail_filename = f"{film.file_id}_maxres.jpg"
                    thumbnail_path = os.path.join(self.thumbnails_dir, 'films', thumbnail_filename)
                    
                    print(f"      📥 Downloading thumbnail: {thumbnail_filename}")
                    
                    # Try maxresdefault first, fallback to hqdefault
                    success = self.download_thumbnail(youtube_info['thumbnail_url'], thumbnail_path)
                    
                    if not success:
                        print(f"      🔄 Fallback to hq thumbnail")
                        success = self.download_thumbnail(youtube_info['thumbnail_hq_url'], thumbnail_path)
                    
                    if success:
                        self.stats['downloaded'] += 1
                        
                        # Update film record
                        film.youtube_id = youtube_info['youtube_id']
                        film.youtube_url = youtube_info['youtube_url']
                        film.thumbnail_url = f"/static/thumbnails/films/{thumbnail_filename}"
                        film.thumbnail_high_url = youtube_info['thumbnail_hq_url']
                        film.thumbnail_medium_url = youtube_info['thumbnail_med_url']
                        film.save()
                        
                        print(f"      ✅ Updated film: {film.title}")
                    else:
                        print(f"      ❌ Failed to download thumbnail")
                        self.stats['errors'] += 1
                else:
                    print(f"      ⚠️ No matching YouTube video found")
                    self.stats['errors'] += 1
                    
            except Exception as e:
                print(f"      ❌ Error processing {film.file_id}: {str(e)}")
                self.stats['errors'] += 1
            
            print()  # Add spacing between films

    def print_summary(self):
        """Print processing summary"""
        print("=" * 60)
        print("BATCH D THUMBNAIL DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Films processed: {self.stats['processed']}")
        print(f"YouTube videos matched: {self.stats['matched']}")
        print(f"Thumbnails downloaded: {self.stats['downloaded']}")
        print(f"Errors: {self.stats['errors']}")

def main():
    downloader = BatchDThumbnailDownloader()
    downloader.process_batch_d_films()
    downloader.print_summary()
    return 0

if __name__ == "__main__":
    sys.exit(main())