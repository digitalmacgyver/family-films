import os
import subprocess
import requests
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import Film, Chapter


class Command(BaseCommand):
    help = 'Generate thumbnails for each chapter based on timestamp'

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

    def handle(self, *args, **options):
        # Create thumbnails directory if it doesn't exist
        thumbnails_dir = os.path.join(settings.BASE_DIR, 'static', 'thumbnails', 'chapters')
        os.makedirs(thumbnails_dir, exist_ok=True)

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
            
            chapters = film.chapters.all().order_by('order')
            if not chapters:
                # If no chapters, generate thumbnails at evenly spaced intervals
                if film.duration:
                    duration_seconds = film.duration.total_seconds()
                    self.generate_interval_thumbnails(film, duration_seconds, thumbnails_dir, options['force'])
                continue
            
            # Generate thumbnails for each chapter
            for chapter in chapters:
                try:
                    success = self.generate_chapter_thumbnail(
                        film, chapter, thumbnails_dir, options['force']
                    )
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(f'  Error generating thumbnail for chapter {chapter.title}: {e}')
            
            # If fewer than 4 chapters, generate additional thumbnails
            if len(chapters) < 4 and film.duration:
                duration_seconds = film.duration.total_seconds()
                additional_needed = 4 - len(chapters)
                self.generate_additional_thumbnails(
                    film, chapters, duration_seconds, additional_needed, thumbnails_dir, options['force']
                )

        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Successfully generated: {success_count} chapter thumbnails')
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))

    def generate_chapter_thumbnail(self, film, chapter, thumbnails_dir, force=False):
        """Generate thumbnail for a specific chapter"""
        thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_{chapter.id}.jpg')
        
        # Skip if thumbnail already exists unless force is True
        if os.path.exists(thumbnail_path) and not force:
            return True
        
        try:
            # For now, use YouTube's built-in thumbnails with some randomization
            # In a production system, you'd want to use ffmpeg to extract frames at specific timestamps
            
            # Use different YouTube thumbnail variants based on chapter order
            variants = ['1', '2', '3', 'default', 'hqdefault', 'mqdefault']
            variant = variants[chapter.order % len(variants)]
            
            thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/{variant}.jpg"
            
            # Download the thumbnail
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            
            # Save the thumbnail
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            
            # Update chapter with thumbnail URL
            relative_path = f'/static/thumbnails/chapters/{film.file_id}_{chapter.id}.jpg'
            chapter.thumbnail_url = relative_path
            chapter.save()
            
            self.stdout.write(f'  ✓ Generated thumbnail for chapter: {chapter.title}')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Failed to generate thumbnail for chapter {chapter.title}: {e}')
            return False

    def generate_interval_thumbnails(self, film, duration_seconds, thumbnails_dir, force=False):
        """Generate thumbnails at evenly spaced intervals for films without chapters"""
        intervals = [0.25, 0.5, 0.75, 0.9]  # 25%, 50%, 75%, 90% through the video
        
        for i, interval in enumerate(intervals):
            timestamp_seconds = int(duration_seconds * interval)
            thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_interval_{i}.jpg')
            
            if os.path.exists(thumbnail_path) and not force:
                continue
            
            try:
                # Use different YouTube thumbnail variants
                variants = ['1', '2', '3', 'default']
                variant = variants[i % len(variants)]
                
                thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/{variant}.jpg"
                
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                self.stdout.write(f'  ✓ Generated interval thumbnail at {interval*100}%')
                
            except Exception as e:
                self.stdout.write(f'  ✗ Failed to generate interval thumbnail: {e}')

    def generate_additional_thumbnails(self, film, chapters, duration_seconds, additional_needed, thumbnails_dir, force=False):
        """Generate additional thumbnails to reach minimum of 4"""
        # Find gaps between chapters where we can add thumbnails
        chapter_times = [ch.start_time_seconds for ch in chapters]
        chapter_times.append(int(duration_seconds))  # Add end time
        
        for i in range(additional_needed):
            # Place thumbnails in the largest gaps
            gap_index = i % len(chapter_times)
            if gap_index < len(chapter_times) - 1:
                gap_start = chapter_times[gap_index] if gap_index == 0 else chapter_times[gap_index]
                gap_end = chapter_times[gap_index + 1]
                timestamp = (gap_start + gap_end) // 2
            else:
                timestamp = int(duration_seconds * 0.9)  # Near the end
            
            thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_extra_{i}.jpg')
            
            if os.path.exists(thumbnail_path) and not force:
                continue
            
            try:
                variants = ['2', '3', 'hqdefault', 'mqdefault']
                variant = variants[i % len(variants)]
                
                thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/{variant}.jpg"
                
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()
                
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                self.stdout.write(f'  ✓ Generated additional thumbnail #{i+1}')
                
            except Exception as e:
                self.stdout.write(f'  ✗ Failed to generate additional thumbnail: {e}')