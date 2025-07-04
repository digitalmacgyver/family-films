import os
import subprocess
import tempfile
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import Film, Chapter
from PIL import Image


class Command(BaseCommand):
    help = 'Generate sprite sheet thumbnails for films based on chapter timestamps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file-ids',
            type=str,
            nargs='*',
            help='Specific file IDs to process (if not provided, processes all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate thumbnails even if they already exist'
        )
        parser.add_argument(
            '--cleanup-old',
            action='store_true',
            help='Remove old individual chapter thumbnails'
        )

    def handle(self, *args, **options):
        # Create thumbnails directory if it doesn't exist
        previews_dir = os.path.join(settings.BASE_DIR, 'static', 'thumbnails', 'previews')
        os.makedirs(previews_dir, exist_ok=True)

        # Cleanup old chapter thumbnails if requested
        if options['cleanup_old']:
            self.cleanup_old_thumbnails()

        # Get films to process
        if options['file_ids']:
            films = Film.objects.filter(file_id__in=options['file_ids'])
        else:
            films = Film.objects.exclude(youtube_id__startswith='placeholder_')

        self.stdout.write(f'Processing {films.count()} films...')

        success_count = 0
        error_count = 0

        for film in films:
            if not film.youtube_id or film.youtube_id.startswith('placeholder_'):
                continue
                
            self.stdout.write(f'Processing film: {film.title} ({film.file_id})')
            
            try:
                success = self.generate_sprite_thumbnail(film, previews_dir, options['force'])
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(f'  Error generating sprite for {film.file_id}: {e}')

        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Successfully generated: {success_count} sprite thumbnails')
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))

    def generate_sprite_thumbnail(self, film, previews_dir, force=False):
        """Generate sprite sheet thumbnail for a film"""
        sprite_path = os.path.join(previews_dir, f'{film.file_id}_sprite.jpg')
        
        # Skip if sprite already exists unless force is True
        if os.path.exists(sprite_path) and not force:
            self.stdout.write(f'  ⏭ Sprite already exists for {film.file_id}')
            return True
        
        chapters = film.chapters.all().order_by('order')
        
        # Determine timestamps for frame extraction
        if chapters.exists():
            # Use chapter timestamps
            timestamps = []
            for chapter in chapters:
                timestamps.append(chapter.start_time_seconds)
            frame_count = len(timestamps)
            
            # If we have many chapters, limit to key ones
            if frame_count > 8:
                # Take every nth chapter to get around 6-8 frames
                step = max(1, frame_count // 6)
                timestamps = [timestamps[i] for i in range(0, len(timestamps), step)]
                frame_count = len(timestamps)
        else:
            # No chapters - use evenly spaced intervals
            if not film.duration:
                self.stdout.write(f'  ✗ No duration or chapters for {film.file_id}')
                return False
            
            duration_seconds = int(film.duration.total_seconds())
            # Extract frames at 10%, 30%, 50%, 70%, 90%
            percentages = [0.1, 0.3, 0.5, 0.7, 0.9]
            timestamps = [int(duration_seconds * p) for p in percentages]
            frame_count = len(timestamps)
        
        try:
            # Extract frames using ffmpeg
            temp_frames = []
            video_url = f"https://www.youtube.com/watch?v={film.youtube_id}"
            
            for i, timestamp in enumerate(timestamps):
                temp_frame = tempfile.NamedTemporaryFile(suffix=f'_{i}.jpg', delete=False)
                temp_frames.append(temp_frame.name)
                
                # Use yt-dlp to get the actual video URL and ffmpeg to extract frame
                cmd = [
                    'yt-dlp', '--get-url', '--format', 'best[height<=720]',
                    video_url
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        raise Exception(f"yt-dlp failed: {result.stderr}")
                    
                    direct_url = result.stdout.strip()
                    
                    # Extract frame at timestamp using ffmpeg
                    ffmpeg_cmd = [
                        'ffmpeg', '-ss', str(timestamp), '-i', direct_url,
                        '-vframes', '1', '-q:v', '2',
                        '-vf', 'scale=160:90',  # Resize to standard thumbnail size
                        '-y', temp_frame.name
                    ]
                    
                    subprocess.run(ffmpeg_cmd, capture_output=True, timeout=60, check=True)
                    
                except subprocess.TimeoutExpired:
                    self.stdout.write(f'  ⚠ Timeout extracting frame at {timestamp}s')
                    # Create a placeholder frame
                    self.create_placeholder_frame(temp_frame.name)
                except Exception as e:
                    self.stdout.write(f'  ⚠ Failed to extract frame at {timestamp}s: {e}')
                    # Create a placeholder frame
                    self.create_placeholder_frame(temp_frame.name)
            
            # Combine frames into sprite sheet
            frame_width, frame_height = 160, 90
            sprite_width = frame_width * frame_count
            sprite_height = frame_height
            
            sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
            
            for i, frame_path in enumerate(temp_frames):
                try:
                    if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                        frame_image = Image.open(frame_path)
                        frame_image = frame_image.resize((frame_width, frame_height))
                        x_offset = i * frame_width
                        sprite_image.paste(frame_image, (x_offset, 0))
                        frame_image.close()
                    else:
                        # Create placeholder frame
                        placeholder = Image.new('RGB', (frame_width, frame_height), (128, 128, 128))
                        x_offset = i * frame_width
                        sprite_image.paste(placeholder, (x_offset, 0))
                except Exception as e:
                    self.stdout.write(f'  ⚠ Error processing frame {i}: {e}')
                    # Create placeholder frame
                    placeholder = Image.new('RGB', (frame_width, frame_height), (128, 128, 128))
                    x_offset = i * frame_width
                    sprite_image.paste(placeholder, (x_offset, 0))
            
            # Save sprite sheet
            sprite_image.save(sprite_path, 'JPEG', quality=85)
            sprite_image.close()
            
            # Update film with sprite info
            film.preview_sprite_url = f'/static/thumbnails/previews/{film.file_id}_sprite.jpg'
            film.preview_frame_count = frame_count
            film.preview_frame_interval = 0.8  # 800ms between frames
            film.preview_sprite_width = frame_width
            film.preview_sprite_height = frame_height
            film.save()
            
            # Cleanup temporary frames
            for temp_frame in temp_frames:
                try:
                    os.unlink(temp_frame)
                except:
                    pass
            
            self.stdout.write(f'  ✓ Generated sprite with {frame_count} frames for {film.file_id}')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Failed to generate sprite for {film.file_id}: {e}')
            # Cleanup temporary frames
            for temp_frame in temp_frames:
                try:
                    os.unlink(temp_frame)
                except:
                    pass
            return False

    def create_placeholder_frame(self, frame_path):
        """Create a placeholder frame when extraction fails"""
        try:
            placeholder = Image.new('RGB', (160, 90), (64, 64, 64))
            placeholder.save(frame_path, 'JPEG')
            placeholder.close()
        except Exception:
            pass

    def cleanup_old_thumbnails(self):
        """Remove old individual chapter thumbnails"""
        chapters_dir = os.path.join(settings.BASE_DIR, 'static', 'thumbnails', 'chapters')
        if os.path.exists(chapters_dir):
            try:
                files = os.listdir(chapters_dir)
                for file in files:
                    file_path = os.path.join(chapters_dir, file)
                    os.unlink(file_path)
                self.stdout.write(f'Cleaned up {len(files)} old chapter thumbnails')
                
                # Remove the empty directory
                os.rmdir(chapters_dir)
            except Exception as e:
                self.stdout.write(f'Error cleaning up old thumbnails: {e}')