#!/usr/bin/env python3
"""
Batch YouTube Searcher

Systematically searches through the YouTube playlist to find videos matching
Batch D File IDs by checking video descriptions.
"""

import os
import sys
import django
import subprocess
import json
import time

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

class BatchYouTubeSearcher:
    def __init__(self):
        self.youtube_playlist_url = 'https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm'
        self.mapping_file = '/home/viblio/family_films/scripts/batch_d_video_mapping.json'
        self.mappings = []
        self.stats = {
            'videos_checked': 0,
            'matches_found': 0,
            'errors': 0
        }

    def load_existing_mappings(self):
        """Load existing video mappings"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    self.mappings = json.load(f)
                    print(f"✅ Loaded {len(self.mappings)} existing mappings")
        except Exception as e:
            print(f"⚠️ Could not load existing mappings: {e}")
            self.mappings = []

    def save_mappings(self):
        """Save mappings to file"""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            print(f"✅ Saved {len(self.mappings)} mappings to file")
        except Exception as e:
            print(f"❌ Error saving mappings: {e}")

    def get_batch_d_file_ids(self, custom_file_ids=None):
        """Get list of Batch D File IDs that need YouTube matches"""
        if custom_file_ids:
            # Use provided custom list
            target_ids = custom_file_ids
        else:
            # Use database query (original behavior)
            batch_d_films = Film.objects.filter(youtube_id__startswith='placeholder_').values_list('file_id', flat=True)
            target_ids = list(batch_d_films)
        
        # Remove already mapped file IDs
        existing_ids = {mapping['file_id'] for mapping in self.mappings}
        needed_ids = [file_id for file_id in target_ids if file_id not in existing_ids]
        
        return needed_ids

    def fetch_video_description(self, video_id):
        """Fetch video description using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--skip-download',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                video_data = json.loads(result.stdout)
                return {
                    'title': video_data.get('title', ''),
                    'description': video_data.get('description', '')
                }
            else:
                return None
                
        except Exception as e:
            print(f"      ❌ Error fetching {video_id}: {e}")
            return None

    def search_videos_for_file_ids(self, file_ids_to_find):
        """Search through YouTube videos to find matches"""
        print(f"🔍 Searching for {len(file_ids_to_find)} File IDs in YouTube playlist...")
        
        # Load existing video list
        youtube_json_file = '/home/viblio/family_films/scripts/youtube_videos_updated.json'
        
        try:
            with open(youtube_json_file, 'r') as f:
                videos = json.load(f)
                print(f"📋 Found {len(videos)} videos to search through")
        except Exception as e:
            print(f"❌ Could not load video list: {e}")
            return
        
        for i, video in enumerate(videos):
            video_id = video.get('video_id')
            if not video_id:
                continue
                
            self.stats['videos_checked'] += 1
            print(f"[{i+1}/{len(videos)}] Checking: {video.get('title', 'Unknown')[:50]}...")
            
            # Fetch video description
            video_data = self.fetch_video_description(video_id)
            
            if video_data:
                description = video_data['description']
                
                # Check if any of our target File IDs are in this description
                for file_id in file_ids_to_find:
                    if f"File ID: {file_id}" in description:
                        print(f"    ✅ FOUND MATCH: {file_id}")
                        
                        # Add to mappings
                        self.mappings.append({
                            'file_id': file_id,
                            'youtube_id': video_id,
                            'title': video_data['title']
                        })
                        
                        # Remove from search list
                        file_ids_to_find.remove(file_id)
                        self.stats['matches_found'] += 1
                        
                        # Save progress periodically
                        if self.stats['matches_found'] % 5 == 0:
                            self.save_mappings()
                        
                        break
                
                # If we found all file IDs, we can stop
                if not file_ids_to_find:
                    print(f"🎉 Found all File IDs!")
                    break
            else:
                self.stats['errors'] += 1
            
            # Add delay to be nice to YouTube
            time.sleep(1)
            
            # Progress update every 10 videos
            if self.stats['videos_checked'] % 10 == 0:
                print(f"    Progress: {self.stats['videos_checked']} videos checked, {self.stats['matches_found']} matches found")
        
        print(f"\n📋 Remaining File IDs not found: {file_ids_to_find}")

    def print_summary(self):
        """Print search summary"""
        print("\n" + "=" * 60)
        print("YOUTUBE SEARCH SUMMARY")
        print("=" * 60)
        print(f"Videos checked: {self.stats['videos_checked']}")
        print(f"Matches found: {self.stats['matches_found']}")
        print(f"Total mappings: {len(self.mappings)}")
        print(f"Errors: {self.stats['errors']}")

def main():
    print("=== BATCH YOUTUBE SEARCHER ===\n")
    
    # Define the specific Batch D File IDs we need to find
    target_file_ids = [
        "76D-SLD_FROS", "76E-SLD_FROS", "77-SLD_FROS", "RLD-R01_FROS", 
        "RLD-R02_FROS", "SLD-02_FROS", "SLD-03_FROS", "SLD-04_FROS", 
        "SLD-05_FROS", "SLD-06_FROS", "SLD-08_FROS", "SLD-09_FROS", 
        "SLD-10_FROS", "SLD-11_FROS", "SLD-12_FROS", "SLD-13_FROS", 
        "SLD-14_FROS", "SLD-15_FROS", "SLD-16_FROS", "SLD-17_FROS", 
        "SLD-18_FROS", "SLD-19_FROS", "SLD-22_FROS", "SLD-R01_FROS", 
        "SLD-R02_FROS", "SLD-R03_FROS", "SLD-R04_FROS"
    ]
    
    searcher = BatchYouTubeSearcher()
    searcher.load_existing_mappings()
    
    # Get File IDs that still need YouTube matches (filtering out already found ones)
    file_ids_to_find = searcher.get_batch_d_file_ids(target_file_ids)
    
    if not file_ids_to_find:
        print("✅ All target Batch D File IDs already have YouTube mappings!")
        return 0
    
    print(f"🎯 Need to find YouTube videos for {len(file_ids_to_find)} File IDs:")
    for file_id in file_ids_to_find[:10]:  # Show first 10
        print(f"  - {file_id}")
    if len(file_ids_to_find) > 10:
        print(f"  ... and {len(file_ids_to_find) - 10} more")
    print()
    
    # Search for matches
    searcher.search_videos_for_file_ids(file_ids_to_find)
    
    # Save final results
    searcher.save_mappings()
    searcher.print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())