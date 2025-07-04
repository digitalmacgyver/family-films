import os
import subprocess
import json
from urllib.parse import urlparse
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from main.models import Film


class Command(BaseCommand):
    help = 'Generate animated thumbnail sprite sheets from YouTube videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='static/thumbnails/animated/',
            help='Directory to save animated thumbnails'
        )
        parser.add_argument(
            '--frame-count',
            type=int,
            default=10,
            help='Number of frames to extract for animation'
        )
        parser.add_argument(
            '--frame-width',
            type=int,
            default=160,
            help='Width of each frame in pixels'
        )
        parser.add_argument(
            '--frame-height',
            type=int,
            default=90,
            help='Height of each frame in pixels'
        )
        parser.add_argument(
            '--duration-sample',
            type=int,
            default=30,
            help='Duration in seconds to sample from (from middle of video)'
        )
        parser.add_argument(
            '--file-ids',
            type=str,
            nargs='*',
            help='Specific file IDs to process (if not provided, processes all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually generating'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip films that already have animated thumbnails'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        frame_count = options['frame_count']
        frame_width = options['frame_width']
        frame_height = options['frame_height']
        duration_sample = options['duration_sample']
        file_ids = options['file_ids']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be generated'))

        # Check dependencies
        if not self.check_dependencies():
            return

        # Create output directory
        full_output_dir = os.path.join(settings.BASE_DIR, output_dir)
        if not dry_run:
            os.makedirs(full_output_dir, exist_ok=True)

        # Get films to process
        if file_ids:
            films = Film.objects.filter(file_id__in=file_ids).exclude(youtube_id__startswith='placeholder_')
        else:
            films = Film.objects.exclude(youtube_id__startswith='placeholder_')

        if skip_existing:
            films = films.filter(preview_sprite_url='')

        self.stdout.write(f'Processing {films.count()} films...')

        success_count = 0
        error_count = 0

        for film in films:
            try:
                if dry_run:
                    self.stdout.write(f'Would generate animated thumbnail for: {film.file_id}')
                else:
                    success = self.generate_animated_thumbnail(
                        film, full_output_dir, frame_count, 
                        frame_width, frame_height, duration_sample
                    )
                    if success:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Generated animated thumbnail for: {film.file_id}')
                        )
                    else:
                        error_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing {film.file_id}: {str(e)}')
                )

        # Print summary
        if not dry_run:
            self.stdout.write('\n=== SUMMARY ===')
            self.stdout.write(f'Successfully generated: {success_count} animated thumbnails')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))

    def check_dependencies(self):
        """Check if required tools are available"""
        required_tools = ['yt-dlp', 'ffmpeg']
        missing_tools = []

        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)

        if missing_tools:
            self.stdout.write(
                self.style.ERROR(
                    f'Missing required tools: {", ".join(missing_tools)}\n'
                    f'Install with: sudo apt-get install yt-dlp ffmpeg'
                )
            )
            return False

        return True

    def generate_animated_thumbnail(self, film, output_dir, frame_count, 
                                   frame_width, frame_height, duration_sample):
        """Generate animated thumbnail sprite sheet for a film"""
        
        youtube_url = f"https://www.youtube.com/watch?v={film.youtube_id}"
        output_filename = f"{film.file_id}_animated.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # Get video duration first
            duration = self.get_video_duration(youtube_url)
            if not duration:
                self.stdout.write(
                    self.style.WARNING(f'Could not get duration for {film.file_id}')
                )
                return False

            # Calculate start time (middle of video, minus half of sample duration)
            start_time = max(0, (duration / 2) - (duration_sample / 2))
            
            # Generate frames using yt-dlp and ffmpeg
            success = self.create_sprite_sheet(
                youtube_url, output_path, start_time, duration_sample,
                frame_count, frame_width, frame_height
            )
            
            if success:
                # Update film record
                relative_path = f"/{output_dir.replace(str(settings.BASE_DIR), '').lstrip('/')}{output_filename}"
                film.preview_sprite_url = relative_path
                film.preview_frame_count = frame_count
                film.preview_frame_interval = duration_sample / frame_count
                film.preview_sprite_width = frame_width
                film.save()
                
                return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating thumbnail for {film.file_id}: {str(e)}')
            )
            
        return False

    def get_video_duration(self, youtube_url):
        """Get video duration using yt-dlp"""
        try:
            cmd = [
                'yt-dlp', '--print', 'duration',
                '--no-download', youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
            
        except (subprocess.CalledProcessError, ValueError):
            return None

    def create_sprite_sheet(self, youtube_url, output_path, start_time, 
                          duration_sample, frame_count, frame_width, frame_height):
        """Create sprite sheet using yt-dlp and ffmpeg"""
        
        try:
            # Calculate frame interval
            frame_interval = duration_sample / frame_count
            
            # Create temporary directory for individual frames
            temp_dir = f"/tmp/frames_{os.path.basename(output_path).split('.')[0]}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract frames using yt-dlp and ffmpeg
            cmd = [
                'yt-dlp', youtube_url,
                '--format', 'best[height<=720]',
                '--exec', f'ffmpeg -i {{}} -ss {start_time} -t {duration_sample} '
                         f'-vf "fps=1/{frame_interval},scale={frame_width}:{frame_height}" '
                         f'{temp_dir}/frame_%03d.jpg'
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Create sprite sheet using ffmpeg
            sprite_cmd = [
                'ffmpeg', '-y',
                '-pattern_type', 'glob',
                '-i', f'{temp_dir}/frame_*.jpg',
                '-filter_complex', f'tile={frame_count}x1',
                output_path
            ]
            
            subprocess.run(sprite_cmd, capture_output=True, check=True)
            
            # Clean up temporary files
            subprocess.run(['rm', '-rf', temp_dir])
            
            return os.path.exists(output_path)
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Command failed: {" ".join(e.cmd) if hasattr(e, "cmd") else str(e)}')
            )
            return False