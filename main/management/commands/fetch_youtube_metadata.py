import os
import json
import re
import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Fetch YouTube video metadata including descriptions using YouTube Data API v3'

    def add_arguments(self, parser):
        parser.add_argument(
            'video_ids',
            nargs='*',
            type=str,
            help='YouTube video IDs to fetch (e.g., YFIDOmMvxiY)'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='YouTube Data API key (or set YOUTUBE_API_KEY environment variable)'
        )
        parser.add_argument(
            '--playlist-id',
            type=str,
            default='PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm',
            help='YouTube playlist ID to fetch all videos from'
        )
        parser.add_argument(
            '--fetch-all',
            action='store_true',
            help='Fetch all videos from the playlist'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            default='youtube_metadata.json',
            help='Output file for video metadata'
        )

    def handle(self, *args, **options):
        video_ids = options['video_ids']
        api_key = options['api_key'] or os.environ.get('YOUTUBE_API_KEY')
        playlist_id = options['playlist_id']
        fetch_all = options['fetch_all']
        output_file = options['output_file']

        if not api_key:
            self.stdout.write(self.style.ERROR(
                'YouTube API key required. Provide via --api-key or YOUTUBE_API_KEY environment variable.\n'
                'Get a key from: https://console.cloud.google.com/apis/credentials'
            ))
            return

        if fetch_all:
            # Fetch all videos from playlist
            videos_data = self.fetch_playlist_videos(playlist_id, api_key)
        elif video_ids:
            # Fetch specific videos
            videos_data = self.fetch_videos_by_id(video_ids, api_key)
        else:
            raise CommandError('Provide video IDs or use --fetch-all to get entire playlist')

        # Extract File IDs from descriptions
        self.process_video_metadata(videos_data)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(videos_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(
            f'Saved metadata for {len(videos_data)} videos to {output_file}'
        ))

    def fetch_videos_by_id(self, video_ids, api_key):
        """Fetch video metadata for specific video IDs"""
        videos_data = []
        
        # YouTube API allows up to 50 video IDs per request
        chunk_size = 50
        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i:i + chunk_size]
            
            url = 'https://www.googleapis.com/youtube/v3/videos'
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': ','.join(chunk),
                'key': api_key
            }
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    video_info = self.extract_video_info(item)
                    videos_data.append(video_info)
                    
                    # Display progress
                    self.stdout.write(f'Fetched: {video_info["video_id"]} - {video_info["title"][:60]}...')
                    if video_info.get('file_id'):
                        self.stdout.write(self.style.SUCCESS(f'  File ID: {video_info["file_id"]}'))
                    else:
                        self.stdout.write(self.style.WARNING('  No File ID found in description'))
                    
            except requests.RequestException as e:
                raise CommandError(f'API request failed: {e}')
        
        return videos_data

    def fetch_playlist_videos(self, playlist_id, api_key):
        """Fetch all videos from a playlist"""
        videos_data = []
        next_page_token = None
        
        while True:
            url = 'https://www.googleapis.com/youtube/v3/playlistItems'
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'key': api_key,
                'maxResults': 50
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Get video IDs from playlist items
                video_ids = []
                for item in data.get('items', []):
                    video_id = item['snippet']['resourceId']['videoId']
                    video_ids.append(video_id)
                
                # Fetch full video details
                if video_ids:
                    batch_data = self.fetch_videos_by_id(video_ids, api_key)
                    videos_data.extend(batch_data)
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except requests.RequestException as e:
                raise CommandError(f'API request failed: {e}')
        
        return videos_data

    def extract_video_info(self, item):
        """Extract relevant information from video data"""
        snippet = item['snippet']
        
        video_info = {
            'video_id': item['id'],
            'title': snippet['title'],
            'description': snippet['description'],
            'published_at': snippet['publishedAt'],
            'channel_title': snippet['channelTitle'],
            'duration': item.get('contentDetails', {}).get('duration'),
            'view_count': item.get('statistics', {}).get('viewCount'),
            'url': f'https://www.youtube.com/watch?v={item["id"]}'
        }
        
        # Extract File ID from description
        file_id_match = re.search(r'File ID:\s*([^\s\n]+)', snippet['description'], re.IGNORECASE)
        if file_id_match:
            video_info['file_id'] = file_id_match.group(1).strip()
        
        # Extract other metadata
        video_info['chapters'] = self.extract_chapters(snippet['description'])
        video_info['people'] = self.extract_field(snippet['description'], 'People')
        video_info['years'] = self.extract_field(snippet['description'], 'Years')
        video_info['locations'] = self.extract_field(snippet['description'], 'Locations')
        video_info['technical_notes'] = self.extract_field(snippet['description'], 'Technical Notes')
        
        return video_info

    def extract_chapters(self, description):
        """Extract chapter information from description"""
        chapters = []
        
        # Look for chapters section
        chapters_match = re.search(r'Chapters?:(.*?)(?=\n\n|\nPeople:|\nYears:|\nLocations:|\nTechnical|\Z)', 
                                  description, re.IGNORECASE | re.DOTALL)
        
        if chapters_match:
            chapters_text = chapters_match.group(1)
            # Extract timestamp and title pairs
            chapter_pattern = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)')
            
            for match in chapter_pattern.finditer(chapters_text):
                timestamp, title = match.groups()
                chapters.append({
                    'timestamp': timestamp,
                    'title': title.strip()
                })
        
        return chapters

    def extract_field(self, description, field_name):
        """Extract a specific field from description"""
        pattern = rf'{field_name}:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|\Z)'
        match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return None

    def process_video_metadata(self, videos_data):
        """Process and display summary of video metadata"""
        self.stdout.write('\n=== VIDEO METADATA SUMMARY ===\n')
        
        total_videos = len(videos_data)
        videos_with_file_id = sum(1 for v in videos_data if v.get('file_id'))
        
        self.stdout.write(f'Total videos: {total_videos}')
        self.stdout.write(f'Videos with File ID: {videos_with_file_id}')
        self.stdout.write(f'Videos without File ID: {total_videos - videos_with_file_id}')
        
        # Show videos without File IDs
        if total_videos > videos_with_file_id:
            self.stdout.write('\nVideos missing File ID:')
            for video in videos_data:
                if not video.get('file_id'):
                    self.stdout.write(f'  - {video["video_id"]}: {video["title"][:60]}...')