import os
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Film, Chapter
from pathlib import Path


class Command(BaseCommand):
    help = 'Update chapter thumbnail URLs to use the new extracted images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--film',
            type=str,
            help='Update only a specific film by file_id',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        film_id = options['film']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Get the thumbnail directory
        thumbnail_dir = Path('static/thumbnails/chapters')
        
        # Get films to process
        if film_id:
            films = Film.objects.filter(file_id=film_id)
        else:
            films = Film.objects.all()
        
        total_updated = 0
        
        for film in films:
            chapters = film.chapters.all().order_by('order')
            if not chapters:
                continue
                
            self.stdout.write(f"\nProcessing film: {film.file_id} - {film.title}")
            
            # Look for new chapter images with pattern: {file_id} - *_image_{number}.jpg
            # We match on file_id prefix since titles might not match exactly
            
            # Find all matching images
            matching_images = []
            try:
                for file in thumbnail_dir.iterdir():
                    if (file.name.startswith(f"{film.file_id} - ") and 
                        "_image_" in file.name and 
                        file.suffix == '.jpg'):
                        matching_images.append(file)
            except Exception as e:
                self.stderr.write(f"Error listing directory: {e}")
                continue
            
            # Sort images by the number after _image_
            matching_images.sort(key=lambda x: int(x.stem.split('_image_')[-1]))
            
            if not matching_images:
                self.stdout.write(f"  No new chapter images found for {film.file_id}")
                continue
            
            self.stdout.write(f"  Found {len(matching_images)} chapter images")
            
            # Update chapters with new thumbnail URLs
            with transaction.atomic():
                for idx, chapter in enumerate(chapters):
                    if idx < len(matching_images):
                        old_url = chapter.thumbnail_url
                        new_url = f"/static/thumbnails/chapters/{matching_images[idx].name}"
                        
                        if old_url != new_url:
                            self.stdout.write(f"  Chapter {idx + 1}: {chapter.title}")
                            self.stdout.write(f"    Old: {old_url}")
                            self.stdout.write(f"    New: {new_url}")
                            
                            if not dry_run:
                                chapter.thumbnail_url = new_url
                                chapter.save()
                            
                            total_updated += 1
                    else:
                        self.stdout.write(f"  Chapter {idx + 1}: No matching image (keeping existing)")
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal chapters updated: {total_updated}"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes were saved'))