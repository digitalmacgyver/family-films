import os
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Film, Chapter
from pathlib import Path
import re

class Command(BaseCommand):
    help = 'Update chapter thumbnails to use the properly extracted images from LibreOffice conversion'

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
        
        # Get the proper thumbnails directory
        proper_dir = Path('static/thumbnails/chapters_proper')
        
        if not proper_dir.exists():
            self.stderr.write(f'Proper thumbnails directory not found: {proper_dir}')
            return
        
        # Get films to process
        if film_id:
            films = Film.objects.filter(file_id=film_id)
        else:
            films = Film.objects.all()
        
        total_updated = 0
        films_with_updates = 0
        
        self.stdout.write(f'Found {len(list(proper_dir.glob("*_proper_image_*.jpg")))} proper thumbnail images')
        
        for film in films:
            chapters = film.chapters.all().order_by('order')
            if not chapters:
                continue
                
            self.stdout.write(f"\nProcessing film: {film.file_id} - {film.title}")
            
            # Find proper images for this film
            # Pattern: {film_id} - {sheet_name}_proper_image_{number}.jpg
            proper_images = []
            for image_file in proper_dir.iterdir():
                if (image_file.name.startswith(f"{film.file_id} - ") and 
                    "_proper_image_" in image_file.name and 
                    image_file.suffix == '.jpg'):
                    proper_images.append(image_file)
            
            # Sort images by the number after _proper_image_
            proper_images.sort(key=lambda x: int(x.stem.split('_proper_image_')[-1]))
            
            if not proper_images:
                self.stdout.write(f"  No proper images found for {film.file_id}")
                continue
            
            self.stdout.write(f"  Found {len(proper_images)} proper images")
            
            # Update chapters with proper thumbnail URLs
            updated_chapters = 0
            with transaction.atomic():
                for idx, chapter in enumerate(chapters):
                    if idx < len(proper_images):
                        old_url = chapter.thumbnail_url
                        new_url = f"/static/thumbnails/chapters_proper/{proper_images[idx].name}"
                        
                        if old_url != new_url:
                            self.stdout.write(f"  Chapter {idx + 1}: {chapter.title}")
                            self.stdout.write(f"    Old: {old_url}")
                            self.stdout.write(f"    New: {new_url}")
                            
                            if not dry_run:
                                chapter.thumbnail_url = new_url
                                chapter.save()
                            
                            updated_chapters += 1
                            total_updated += 1
                    else:
                        self.stdout.write(f"  Chapter {idx + 1}: No matching proper image (keeping existing)")
            
            if updated_chapters > 0:
                films_with_updates += 1
            
            self.stdout.write(f"  Updated {updated_chapters} chapters for this film")
        
        self.stdout.write(self.style.SUCCESS(f"\nSUMMARY:"))
        self.stdout.write(f"Films processed: {films.count()}")
        self.stdout.write(f"Films with updates: {films_with_updates}")
        self.stdout.write(f"Total chapters updated: {total_updated}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes were saved'))
            
        # Show a sample of the changes
        self.stdout.write(f"\nSample proper image files:")
        sample_images = list(proper_dir.glob("*_proper_image_*.jpg"))[:5]
        for img in sample_images:
            self.stdout.write(f"  {img.name}")