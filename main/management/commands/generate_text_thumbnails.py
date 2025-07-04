import os
import random
from PIL import Image, ImageDraw, ImageFont
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import Film, Chapter
import textwrap


class Command(BaseCommand):
    help = 'Generate text-based thumbnails for each chapter with title and timestamp'

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
            films = Film.objects.all()

        self.stdout.write(f'Processing {films.count()} films...')

        # Define color palette for backgrounds
        self.colors = [
            '#FF6B6B',  # Soft red
            '#4ECDC4',  # Teal
            '#45B7D1',  # Sky blue
            '#96CEB4',  # Mint green
            '#F7DC6F',  # Soft yellow
            '#BB8FCE',  # Lavender
            '#85C1E9',  # Light blue
            '#F8B500',  # Orange
            '#6C5CE7',  # Purple
            '#A8E6CF',  # Pale green
            '#FFD93D',  # Golden yellow
            '#FF8B94',  # Coral
        ]

        success_count = 0
        error_count = 0

        for film in films:
            self.stdout.write(f'Processing film: {film.title} ({film.file_id})')
            
            chapters = film.chapters.all().order_by('order')
            if not chapters:
                # If no chapters, generate thumbnails with film info
                self.generate_film_thumbnails(film, thumbnails_dir, options['force'])
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
            if len(chapters) < 4:
                additional_needed = 4 - len(chapters)
                self.generate_additional_thumbnails(
                    film, len(chapters), additional_needed, thumbnails_dir, options['force']
                )

        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Successfully generated: {success_count} chapter thumbnails')
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Errors: {error_count}'))

    def generate_chapter_thumbnail(self, film, chapter, thumbnails_dir, force=False):
        """Generate text-based thumbnail for a specific chapter"""
        thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_{chapter.id}.jpg')
        
        # Skip if thumbnail already exists unless force is True
        if os.path.exists(thumbnail_path) and not force:
            return True
        
        try:
            # Create thumbnail image
            img = self.create_text_thumbnail(
                chapter.title,
                chapter.start_time,
                f"Chapter {chapter.order}",
                chapter.order - 1  # Use order for consistent color
            )
            
            # Save the thumbnail
            img.save(thumbnail_path, 'JPEG', quality=90)
            
            # Update chapter with thumbnail URL
            relative_path = f'/static/thumbnails/chapters/{film.file_id}_{chapter.id}.jpg'
            chapter.thumbnail_url = relative_path
            chapter.save()
            
            self.stdout.write(f'  ✓ Generated thumbnail for chapter: {chapter.title}')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Failed to generate thumbnail for chapter {chapter.title}: {e}')
            return False

    def create_text_thumbnail(self, title, timestamp, subtitle="", color_index=0):
        """Create a text-based thumbnail image"""
        # Image dimensions (16:9 aspect ratio)
        width = 640
        height = 360
        
        # Select background color
        bg_color = self.colors[color_index % len(self.colors)]
        
        # Create image with colored background
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a nice font, fall back to default
        try:
            # Try common font paths
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                'C:\\Windows\\Fonts\\Arial.ttf'
            ]
            title_font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    title_font = ImageFont.truetype(font_path, 36)
                    time_font = ImageFont.truetype(font_path, 48)
                    subtitle_font = ImageFont.truetype(font_path, 24)
                    break
            
            if not title_font:
                # Fall back to default font
                title_font = ImageFont.load_default()
                time_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Draw timestamp at the top
        timestamp_text = timestamp
        if hasattr(time_font, 'getbbox'):
            bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
            time_width = bbox[2] - bbox[0]
        else:
            time_width, _ = draw.textsize(timestamp_text, font=time_font)
        time_x = (width - time_width) // 2
        draw.text((time_x, 40), timestamp_text, fill='white', font=time_font)
        
        # Draw subtitle if provided
        if subtitle:
            if hasattr(subtitle_font, 'getbbox'):
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
            else:
                subtitle_width, _ = draw.textsize(subtitle, font=subtitle_font)
            subtitle_x = (width - subtitle_width) // 2
            draw.text((subtitle_x, 100), subtitle, fill='white', font=subtitle_font)
        
        # Wrap and draw title text (use same logic as sprites for consistency)
        wrapped_text = textwrap.fill(title, width=15)
        lines = wrapped_text.split('\n')
        
        # Limit to 3 lines for consistency with sprites
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:12] + '...' if len(lines[2]) > 12 else lines[2]
        
        # Calculate starting Y position to center the text block
        line_height = 40
        text_block_height = len(lines) * line_height
        start_y = (height - text_block_height) // 2 + 20
        
        # Draw each line of wrapped text
        for i, line in enumerate(lines):
            if hasattr(title_font, 'getbbox'):
                bbox = draw.textbbox((0, 0), line, font=title_font)
                text_width = bbox[2] - bbox[0]
            else:
                text_width, _ = draw.textsize(line, font=title_font)
            text_x = (width - text_width) // 2
            text_y = start_y + i * line_height
            
            # Draw text with shadow for better readability
            shadow_offset = 2
            draw.text((text_x + shadow_offset, text_y + shadow_offset), line, 
                     fill='black', font=title_font)
            draw.text((text_x, text_y), line, fill='white', font=title_font)
        
        return img

    def generate_film_thumbnails(self, film, thumbnails_dir, force=False):
        """Generate thumbnails for films without chapters"""
        for i in range(4):
            thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_film_{i}.jpg')
            
            if os.path.exists(thumbnail_path) and not force:
                continue
            
            try:
                img = self.create_text_thumbnail(
                    film.title,
                    f"Part {i+1}",
                    "Film Preview",
                    i
                )
                img.save(thumbnail_path, 'JPEG', quality=90)
                self.stdout.write(f'  ✓ Generated film thumbnail #{i+1}')
            except Exception as e:
                self.stdout.write(f'  ✗ Failed to generate film thumbnail: {e}')

    def generate_additional_thumbnails(self, film, start_index, count, thumbnails_dir, force=False):
        """Generate additional thumbnails to reach minimum of 4"""
        for i in range(count):
            thumbnail_path = os.path.join(thumbnails_dir, f'{film.file_id}_extra_{i}.jpg')
            
            if os.path.exists(thumbnail_path) and not force:
                continue
            
            try:
                img = self.create_text_thumbnail(
                    film.title,
                    f"Scene {start_index + i + 1}",
                    "Additional Content",
                    start_index + i
                )
                img.save(thumbnail_path, 'JPEG', quality=90)
                self.stdout.write(f'  ✓ Generated additional thumbnail #{i+1}')
            except Exception as e:
                self.stdout.write(f'  ✗ Failed to generate additional thumbnail: {e}')