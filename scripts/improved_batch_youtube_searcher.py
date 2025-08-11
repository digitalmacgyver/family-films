#!/usr/bin/env python3
"""
Improved Batch YouTube Searcher

Systematically searches through the YouTube playlist to find videos matching
Batch D File IDs by checking video descriptions with better error handling
and full description retrieval.
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

class ImprovedBatchYouTubeSearcher:
    def __init__(self):
        self.youtube_playlist_url = 'https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm'
        self.mapping_file = '/home/viblio/family_films/scripts/batch_d_video_mapping.json'
        self.mappings = []
        self.stats = {
            'videos_checked': 0,
            'matches_found': 0,
            'errors': 0,
            'retries': 0
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

    def get_batch_d_file_ids(self):
        """Get list of Batch D File IDs that need YouTube matches"""
        # Define the specific Batch D File IDs we need to find
        target_file_ids = [
            "76D-SLD_FROS", "76E-SLD_FROS", "77-SLD_FROS", "RLD-R01_FROS", 
            "RLD-R02_FROS", "SLD-01_FROS", "SLD-02_FROS", "SLD-03_FROS", 
            "SLD-04_FROS", "SLD-05_FROS", "SLD-06_FROS", "SLD-07_FROS", 
            "SLD-08_FROS", "SLD-09_FROS", "SLD-10_FROS", "SLD-11_FROS", 
            "SLD-12_FROS", "SLD-13_FROS", "SLD-14_FROS", "SLD-15_FROS", 
            "SLD-16_FROS", "SLD-17_FROS", "SLD-18_FROS", "SLD-19_FROS", 
            "SLD-20_FROS", "SLD-21_FROS", "SLD-22_FROS", "SLD-R01_FROS", 
            "SLD-R02_FROS", "SLD-R03_FROS", "SLD-R04_FROS", "75-SLD_FROS",
            "76A-SLD_FROS", "76B-SLD_FROS", "76C-SLD_FROS"
        ]
        
        # Remove already mapped file IDs
        existing_ids = {mapping['file_id'] for mapping in self.mappings}
        needed_ids = [file_id for file_id in target_file_ids if file_id not in existing_ids]
        
        return needed_ids

    def fetch_video_description_robust(self, video_id, max_retries=3):
        """Fetch video description using yt-dlp with robust error handling"""
        for attempt in range(max_retries):
            try:
                # Use more conservative yt-dlp options
                cmd = [
                    'yt-dlp',
                    '--dump-json',
                    '--skip-download',
                    '--no-warnings',
                    '--quiet',
                    '--ignore-errors',
                    f'https://www.youtube.com/watch?v={video_id}'
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=45  # Longer timeout
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        video_data = json.loads(result.stdout)
                        return {
                            'title': video_data.get('title', ''),
                            'description': video_data.get('description', ''),
                            'success': True
                        }
                    except json.JSONDecodeError:
                        print(f"      ⚠️ JSON decode error for {video_id} (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                else:
                    if attempt < max_retries - 1:
                        print(f"      ⚠️ API error for {video_id} (attempt {attempt + 1}), retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        self.stats['retries'] += 1
                        continue
                        
                return {'success': False, 'error': f'Failed after {max_retries} attempts'}
                
            except subprocess.TimeoutExpired:
                print(f"      ⏰ Timeout for {video_id} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"      ❌ Unexpected error for {video_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                    
        return {'success': False, 'error': 'Max retries exceeded'}

    def search_videos_for_file_ids(self, file_ids_to_find):
        """Search through YouTube videos to find matches"""
        print(f"🔍 Searching for {len(file_ids_to_find)} File IDs in YouTube playlist...")
        
        # Load video list
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
            title = video.get('title', 'Unknown')[:60]
            print(f"[{i+1:2d}/{len(videos)}] Checking: {title}...")
            
            # Fetch video description with robust error handling
            result = self.fetch_video_description_robust(video_id)
            
            if result.get('success'):
                description = result['description']
                video_title = result['title']
                
                # Check if any of our target File IDs are in this description
                found_ids = []
                for file_id in file_ids_to_find:
                    if f"File ID: {file_id}" in description:
                        found_ids.append(file_id)
                
                if found_ids:
                    print(f"    ✅ FOUND {len(found_ids)} MATCH(ES): {', '.join(found_ids)}")
                    
                    # Add to mappings
                    for file_id in found_ids:
                        self.mappings.append({
                            'file_id': file_id,
                            'youtube_id': video_id,
                            'title': video_title
                        })
                        
                        # Remove from search list
                        file_ids_to_find.remove(file_id)
                        self.stats['matches_found'] += 1
                    
                    # Save progress after every match
                    self.save_mappings()
                
                # If we found all file IDs, we can stop
                if not file_ids_to_find:
                    print(f"🎉 Found all File IDs!")
                    break
            else:
                self.stats['errors'] += 1
                print(f"    ❌ Error: {result.get('error', 'Unknown error')}")
            
            # Progressive delay - slower for errors, faster for successes
            if result.get('success'):
                time.sleep(0.5)  # Faster for successful requests
            else:
                time.sleep(2)  # Longer delay after errors
            
            # Progress update every 10 videos
            if self.stats['videos_checked'] % 10 == 0:
                remaining = len(file_ids_to_find)
                print(f"    📊 Progress: {self.stats['videos_checked']} checked, {self.stats['matches_found']} found, {remaining} remaining")
        
        print(f"\n📋 Remaining File IDs not found ({len(file_ids_to_find)}): {file_ids_to_find}")

    def print_summary(self):
        """Print search summary"""
        print("\n" + "=" * 60)
        print("IMPROVED YOUTUBE SEARCH SUMMARY")
        print("=" * 60)
        print(f"Videos checked: {self.stats['videos_checked']}")
        print(f"Matches found: {self.stats['matches_found']}")
        print(f"Total mappings: {len(self.mappings)}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Retries: {self.stats['retries']}")

def main():
    print("=== IMPROVED BATCH YOUTUBE SEARCHER ===\n")
    
    searcher = ImprovedBatchYouTubeSearcher()
    searcher.load_existing_mappings()
    
    # Get File IDs that still need YouTube matches
    file_ids_to_find = searcher.get_batch_d_file_ids()
    
    if not file_ids_to_find:
        print("✅ All Batch D File IDs already have YouTube mappings!")
        return 0
    
    print(f"🎯 Need to find YouTube videos for {len(file_ids_to_find)} File IDs:")
    for i, file_id in enumerate(file_ids_to_find):
        print(f"  {i+1:2d}. {file_id}")
    print()
    
    # Search for matches
    searcher.search_videos_for_file_ids(file_ids_to_find)
    
    # Save final results
    searcher.save_mappings()
    searcher.print_summary()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())