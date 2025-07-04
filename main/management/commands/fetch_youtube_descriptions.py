import json
import re
import subprocess
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Fetch YouTube video descriptions using yt-dlp (no API key required)'

    def add_arguments(self, parser):
        parser.add_argument(
            'video_ids',
            nargs='*',
            type=str,
            help='YouTube video IDs or URLs to fetch'
        )
        parser.add_argument(
            '--playlist-url',
            type=str,
            default='https://www.youtube.com/playlist?list=PLK3iapm6jnkkDIa9IzKV7eP17HS4vdlCm',
            help='YouTube playlist URL to fetch all videos from'
        )
        parser.add_argument(
            '--fetch-all',
            action='store_true',
            help='Fetch all videos from the playlist'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            default='youtube_descriptions.json',
            help='Output file for video descriptions'
        )

    def handle(self, *args, **options):
        video_ids = options['video_ids']
        playlist_url = options['playlist_url']
        fetch_all = options['fetch_all']
        output_file = options['output_file']

        # Check if yt-dlp is available
        if not self.check_ytdlp():
            return

        videos_data = []

        if fetch_all:
            # Fetch all videos from playlist
            self.stdout.write(f'Fetching all videos from playlist...')
            videos_data = self.fetch_playlist_metadata(playlist_url)
        elif video_ids:
            # Fetch specific videos
            for video_id in video_ids:
                # Handle both video IDs and full URLs
                if not video_id.startswith('http'):
                    video_url = f'https://www.youtube.com/watch?v={video_id}'
                else:
                    video_url = video_id
                
                self.stdout.write(f'Fetching: {video_url}')
                video_info = self.fetch_video_metadata(video_url)
                if video_info:
                    videos_data.append(video_info)
        else:
            raise CommandError('Provide video IDs/URLs or use --fetch-all')

        # Process and display results
        self.process_videos(videos_data)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(videos_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(
            f'\nSaved metadata for {len(videos_data)} videos to {output_file}'
        ))

    def check_ytdlp(self):
        """Check if yt-dlp is available"""
        try:
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try with local installation
            try:
                subprocess.run(['~/.local/bin/yt-dlp', '--version'], 
                             capture_output=True, check=True, shell=True)
                return True
            except:
                self.stdout.write(self.style.ERROR(
                    'yt-dlp not found. Install with: pip install yt-dlp'
                ))
                return False

    def fetch_video_metadata(self, video_url):
        """Fetch metadata for a single video"""
        try:
            # Use yt-dlp to extract metadata without downloading
            cmd = [
                'yt-dlp', '--dump-json', '--no-download',
                '--no-warnings', video_url
            ]
            
            # Try local installation if main command fails
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                cmd[0] = '~/.local/bin/yt-dlp'
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      check=True, shell=True)
            
            data = json.loads(result.stdout)
            
            # Extract relevant information
            video_info = {
                'video_id': data.get('id'),
                'title': data.get('title'),
                'description': data.get('description', ''),
                'duration': data.get('duration'),
                'upload_date': data.get('upload_date'),
                'uploader': data.get('uploader'),
                'view_count': data.get('view_count'),
                'url': data.get('webpage_url')
            }
            
            # Extract File ID from description
            file_id_match = re.search(r'File ID:\s*([^\s\n]+)', 
                                    video_info['description'], re.IGNORECASE)
            if file_id_match:
                video_info['file_id'] = file_id_match.group(1).strip()
            
            # Extract other metadata
            video_info['chapters'] = self.extract_chapters(video_info['description'])
            video_info['people'] = self.extract_field(video_info['description'], 'People')
            video_info['years'] = self.extract_field(video_info['description'], 'Years')
            video_info['locations'] = self.extract_field(video_info['description'], 'Locations')
            
            return video_info
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch {video_url}: {e}'))
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Failed to parse JSON: {e}'))
            return None

    def fetch_playlist_metadata(self, playlist_url):
        """Fetch metadata for all videos in a playlist"""
        try:
            # First get playlist info
            cmd = [
                'yt-dlp', '--flat-playlist', '--dump-json',
                '--no-warnings', playlist_url
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                cmd[0] = '~/.local/bin/yt-dlp'
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      check=True, shell=True)
            
            videos_data = []
            
            # Process each line (each video is a separate JSON object)
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        entry = json.loads(line)
                        video_url = entry.get('url') or entry.get('webpage_url')
                        
                        if video_url:
                            self.stdout.write(f'Fetching: {entry.get("title", video_url)[:60]}...')
                            video_info = self.fetch_video_metadata(video_url)
                            if video_info:
                                videos_data.append(video_info)
                    except json.JSONDecodeError:
                        continue
            
            return videos_data
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch playlist: {e}'))
            return []

    def extract_chapters(self, description):
        """Extract chapter information from description"""
        chapters = []
        
        # Look for chapters section
        chapters_match = re.search(
            r'Chapters?:(.*?)(?=\n\n|\nPeople:|\nYears:|\nLocations:|\nTechnical|\Z)', 
            description, re.IGNORECASE | re.DOTALL
        )
        
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

    def process_videos(self, videos_data):
        """Process and display summary"""
        self.stdout.write('\n=== RESULTS SUMMARY ===\n')
        
        total = len(videos_data)
        with_file_id = sum(1 for v in videos_data if v.get('file_id'))
        
        self.stdout.write(f'Total videos fetched: {total}')
        self.stdout.write(f'Videos with File ID: {with_file_id}')
        self.stdout.write(f'Videos without File ID: {total - with_file_id}')
        
        # Show File ID mappings
        if with_file_id > 0:
            self.stdout.write('\nFile ID Mappings Found:')
            for video in videos_data:
                if video.get('file_id'):
                    self.stdout.write(
                        f'  {video["video_id"]} -> {video["file_id"]} '
                        f'({video["title"][:40]}...)'
                    )