import re
import requests
from urllib.parse import urlparse, parse_qs
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from main.models import Film


class Command(BaseCommand):
    help = 'Map file IDs to actual YouTube video IDs from playlist'

    def add_arguments(self, parser):
        parser.add_argument(
            '--youtube-playlist',
            type=str,
            default='https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm',
            help='YouTube playlist URL'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='YouTube API key (optional - will use web scraping if not provided)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be mapped without actually updating'
        )

    def handle(self, *args, **options):
        playlist_url = options['youtube_playlist']
        api_key = options['api_key']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be updated'))

        # Extract playlist ID
        playlist_id = self.extract_playlist_id(playlist_url)
        self.stdout.write(f'YouTube Playlist ID: {playlist_id}')

        # Get video data from playlist
        if api_key:
            videos = self.get_videos_via_api(playlist_id, api_key)
        else:
            self.stdout.write(self.style.WARNING('No API key provided, using web scraping method'))
            videos = self.get_videos_via_scraping(playlist_url)

        if not videos:
            raise CommandError('No videos found in playlist')

        self.stdout.write(f'Found {len(videos)} videos in playlist')

        # Map videos to films
        mapped_count = self.map_videos_to_films(videos, dry_run)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully mapped {mapped_count} films'))

    def extract_playlist_id(self, url):
        """Extract playlist ID from YouTube URL"""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        return query_params.get('list', [''])[0]

    def get_videos_via_api(self, playlist_id, api_key):
        """Get video data using YouTube API (requires API key)"""
        videos = []
        next_page_token = None
        
        while True:
            url = f'https://www.googleapis.com/youtube/v3/playlistItems'
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
                
                for item in data.get('items', []):
                    snippet = item['snippet']
                    video_id = snippet['resourceId']['videoId']
                    title = snippet['title']
                    description = snippet['description']
                    
                    # Extract file ID from description
                    file_id = self.extract_file_id_from_description(description)
                    
                    if file_id:
                        videos.append({
                            'video_id': video_id,
                            'title': title,
                            'description': description,
                            'file_id': file_id
                        })
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except requests.RequestException as e:
                raise CommandError(f'API request failed: {e}')
        
        return videos

    def get_videos_via_scraping(self, playlist_url):
        """Get video data via web scraping (fallback method)"""
        # This is a simplified version - in reality you'd need to handle 
        # YouTube's dynamic loading and potentially use selenium
        self.stdout.write(self.style.WARNING(
            'Web scraping method not fully implemented. '
            'Please provide a YouTube API key for best results.'
        ))
        
        # For now, return empty list - user will need to provide API key
        # or manually create the mapping
        return []

    def extract_file_id_from_description(self, description):
        """Extract file ID from video description"""
        # Look for "File ID: [ID]" pattern in description
        match = re.search(r'File ID:\s*([^\s\n]+)', description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def map_videos_to_films(self, videos, dry_run):
        """Map YouTube videos to Film records"""
        mapped_count = 0
        
        for video in videos:
            file_id = video['file_id']
            video_id = video['video_id']
            
            try:
                film = Film.objects.get(file_id=file_id)
                
                if dry_run:
                    self.stdout.write(
                        f'Would map {file_id} -> {video_id} ({video["title"][:50]}...)'
                    )
                else:
                    # Update the film with real YouTube data
                    old_youtube_id = film.youtube_id
                    film.youtube_id = video_id
                    film.youtube_url = f'https://www.youtube.com/watch?v={video_id}'
                    film.thumbnail_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
                    
                    # Also try to get higher quality thumbnails
                    film.thumbnail_high_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                    film.thumbnail_medium_url = f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'
                    
                    film.save()
                    
                    self.stdout.write(
                        f'Mapped {file_id}: {old_youtube_id} -> {video_id}'
                    )
                
                mapped_count += 1
                
            except Film.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Film not found for file_id: {file_id}')
                )
                continue
        
        return mapped_count

    def create_manual_mapping_file(self):
        """Create a CSV file for manual mapping if automatic mapping fails"""
        films = Film.objects.all()
        
        with open('youtube_mapping.csv', 'w') as f:
            f.write('file_id,current_youtube_id,title,new_youtube_id\n')
            
            for film in films:
                f.write(f'{film.file_id},{film.youtube_id},"{film.title}",\n')
        
        self.stdout.write(
            self.style.SUCCESS(
                'Created youtube_mapping.csv for manual mapping. '
                'Fill in the new_youtube_id column and run with --manual-file option.'
            )
        )