import os
import requests
from PIL import Image
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from main.models import Film


class Command(BaseCommand):
    help = 'Generate preview thumbnail sequences from YouTube thumbnails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='static/thumbnails/previews/',
            help='Directory to save preview thumbnails'
        )
        parser.add_argument(
            '--preview-count',
            type=int,
            default=4,
            help='Number of preview images to generate'
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

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        preview_count = options['preview_count']
        file_ids = options['file_ids']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be generated'))

        # Create output directory
        full_output_dir = os.path.join(settings.BASE_DIR, output_dir)
        if not dry_run:
            os.makedirs(full_output_dir, exist_ok=True)

        # Get films to process
        if file_ids:
            films = Film.objects.filter(file_id__in=file_ids).exclude(youtube_id__startswith='placeholder_')
        else:
            films = Film.objects.exclude(youtube_id__startswith='placeholder_')

        self.stdout.write(f'Processing {films.count()} films...')

        success_count = 0
        error_count = 0

        for film in films:
            try:
                if dry_run:
                    self.stdout.write(f'Would generate preview thumbnails for: {film.file_id}')
                else:
                    success = self.generate_preview_thumbnails(
                        film, full_output_dir, preview_count
                    )
                    if success:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Generated preview thumbnails for: {film.file_id}')
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
            self.stdout.write(f'Successfully generated: {success_count} preview sets')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))

    def generate_preview_thumbnails(self, film, output_dir, preview_count):
        """Generate preview thumbnails from YouTube thumbnails"""
        
        # YouTube provides thumbnails at different timestamps
        # We'll use these predefined thumbnail timestamps
        thumbnail_urls = [
            f"https://img.youtube.com/vi/{film.youtube_id}/0.jpg",     # Default
            f"https://img.youtube.com/vi/{film.youtube_id}/1.jpg",     # 25% mark
            f"https://img.youtube.com/vi/{film.youtube_id}/2.jpg",     # 50% mark  
            f"https://img.youtube.com/vi/{film.youtube_id}/3.jpg",     # 75% mark
        ]
        
        # Also try higher quality versions
        hq_urls = [
            f"https://img.youtube.com/vi/{film.youtube_id}/hq1.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/hq2.jpg",
            f"https://img.youtube.com/vi/{film.youtube_id}/hq3.jpg",
        ]
        
        # Combine and limit to requested count
        all_urls = thumbnail_urls + hq_urls
        selected_urls = all_urls[:preview_count]
        
        preview_images = []
        
        for i, url in enumerate(selected_urls):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Save individual thumbnail
                filename = f"{film.file_id}_preview_{i+1}.jpg"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                preview_images.append(filepath)
                
            except requests.RequestException:
                # If we can't get a specific thumbnail, use the default
                try:
                    default_url = f"https://img.youtube.com/vi/{film.youtube_id}/mqdefault.jpg"
                    response = requests.get(default_url, timeout=10)
                    response.raise_for_status()
                    
                    filename = f"{film.file_id}_preview_{i+1}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    preview_images.append(filepath)
                    
                except requests.RequestException:
                    continue
        
        if preview_images:
            # Create sprite sheet
            sprite_path = self.create_sprite_sheet(film, preview_images, output_dir)
            
            if sprite_path:
                # Update film record
                relative_path = sprite_path.replace(str(settings.BASE_DIR), '').lstrip('/')
                film.preview_sprite_url = f"/{relative_path}"
                film.preview_frame_count = len(preview_images)
                film.preview_frame_interval = 0.8  # 800ms between frames
                film.preview_sprite_width = 160    # Standard thumbnail width
                film.preview_sprite_height = 90    # Standard thumbnail height
                film.save()
                
                return True
        
        return False

    def create_sprite_sheet(self, film, image_paths, output_dir):
        """Create a horizontal sprite sheet from individual images"""
        if not image_paths:
            return None
        
        try:
            images = []
            for path in image_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    # Resize to consistent dimensions
                    img = img.resize((160, 90), Image.Resampling.LANCZOS)
                    images.append(img)
            
            if not images:
                return None
            
            # Create sprite sheet
            total_width = sum(img.width for img in images)
            max_height = max(img.height for img in images)
            
            sprite = Image.new('RGB', (total_width, max_height), (0, 0, 0))
            
            x_offset = 0
            for img in images:
                sprite.paste(img, (x_offset, 0))
                x_offset += img.width
            
            # Save sprite sheet
            sprite_filename = f"{film.file_id}_sprite.jpg"
            sprite_path = os.path.join(output_dir, sprite_filename)
            sprite.save(sprite_path, 'JPEG', quality=85)
            
            # Clean up individual images
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
            
            return sprite_path
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sprite sheet for {film.file_id}: {str(e)}')
            )
            return None