import re
import requests
import json
from urllib.parse import urlparse, parse_qs
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Fetch YouTube video data from playlist (basic scraping approach)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--playlist-url',
            type=str,
            default='https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm',
            help='YouTube playlist URL'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            default='youtube_videos.json',
            help='Output JSON file with video data'
        )

    def handle(self, *args, **options):
        playlist_url = options['playlist_url']
        output_file = options['output_file']

        self.stdout.write(f'Fetching playlist: {playlist_url}')
        
        try:
            # Fetch the playlist page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(playlist_url, headers=headers)
            response.raise_for_status()
            
            # Extract video data from the page
            videos = self.extract_videos_from_page(response.text)
            
            if videos:
                # Save to JSON file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(videos, f, indent=2, ensure_ascii=False)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Found {len(videos)} videos, saved to {output_file}')
                )
                
                # Show first few videos
                self.stdout.write('\nFirst few videos found:')
                for video in videos[:5]:
                    self.stdout.write(f'  {video["video_id"]}: {video["title"][:60]}...')
                    
            else:
                self.stdout.write(
                    self.style.WARNING('No videos found. This may be due to YouTube\'s dynamic loading.')
                )
                
        except requests.RequestException as e:
            raise CommandError(f'Failed to fetch playlist: {e}')

    def extract_videos_from_page(self, html_content):
        """Extract video information from YouTube playlist page HTML"""
        videos = []
        
        # Look for video data in the page
        # YouTube embeds video data in JSON within script tags
        
        # Pattern to find video IDs and titles
        video_pattern = re.compile(r'"videoId":"([^"]+)".*?"title":{"runs":\[{"text":"([^"]+)"}\]', re.DOTALL)
        matches = video_pattern.findall(html_content)
        
        # Alternative pattern for simpler extraction
        if not matches:
            # Look for videoId patterns
            video_id_pattern = re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"')
            video_ids = video_id_pattern.findall(html_content)
            
            # Look for title patterns
            title_pattern = re.compile(r'"title":"([^"]+)"')
            titles = title_pattern.findall(html_content)
            
            # Try to match them up (this is imperfect but better than nothing)
            min_length = min(len(video_ids), len(titles))
            matches = list(zip(video_ids[:min_length], titles[:min_length]))
        
        for video_id, title in matches:
            # Clean up the title
            title = title.replace('\\u0026', '&').replace('\\/', '/')
            
            videos.append({
                'video_id': video_id,
                'title': title,
                'url': f'https://www.youtube.com/watch?v={video_id}'
            })
        
        # Remove duplicates based on video_id
        seen_ids = set()
        unique_videos = []
        for video in videos:
            if video['video_id'] not in seen_ids:
                seen_ids.add(video['video_id'])
                unique_videos.append(video)
        
        return unique_videos