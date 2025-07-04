import os
import tempfile
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import Film, Chapter
from PIL import Image, ImageDraw, ImageFont
import textwrap


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
            films = Film.objects.all()

        self.stdout.write(f'Processing {films.count()} films...')

        # Define color palette for text thumbnails (same as generate_text_thumbnails)
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
        """Generate sprite sheet thumbnail for a film using text-based frames"""
        sprite_path = os.path.join(previews_dir, f'{film.file_id}_sprite.jpg')
        
        # Skip if sprite already exists unless force is True
        if os.path.exists(sprite_path) and not force:
            self.stdout.write(f'  ⏭ Sprite already exists for {film.file_id}')
            return True
        
        chapters = film.chapters.all().order_by('order')
        
        # Determine content for frame generation
        if chapters.exists():
            # Use chapters for frames
            frame_data = []
            for chapter in chapters:
                frame_data.append({
                    'title': chapter.title,
                    'timestamp': chapter.start_time,
                    'subtitle': f"Chapter {chapter.order}",
                    'color_index': chapter.order - 1
                })
            frame_count = len(frame_data)
            
            # If we have many chapters, limit to key ones
            if frame_count > 8:
                # Take every nth chapter to get around 6-8 frames
                step = max(1, frame_count // 6)
                frame_data = [frame_data[i] for i in range(0, len(frame_data), step)]
                frame_count = len(frame_data)
        else:
            # No chapters - use film title with different time markers
            frame_data = []
            for i in range(4):  # Generate 4 frames for films without chapters
                frame_data.append({
                    'title': film.title,
                    'timestamp': f"Part {i+1}",
                    'subtitle': "Film Preview",
                    'color_index': i
                })
            frame_count = len(frame_data)
        
        try:
            # Generate text-based frames
            frame_width, frame_height = 160, 90
            frames = []
            
            for i, data in enumerate(frame_data):
                frame_image = self.create_text_thumbnail(
                    data['title'],
                    data['timestamp'],
                    data['subtitle'],
                    data['color_index'],
                    frame_width,
                    frame_height
                )
                frames.append(frame_image)
            
            # Combine frames into sprite sheet
            sprite_width = frame_width * frame_count
            sprite_height = frame_height
            
            sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
            
            for i, frame_image in enumerate(frames):
                x_offset = i * frame_width
                sprite_image.paste(frame_image, (x_offset, 0))
                frame_image.close()
            
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
            
            self.stdout.write(f'  ✓ Generated sprite with {frame_count} frames for {film.file_id}')
            return True
            
        except Exception as e:
            self.stdout.write(f'  ✗ Failed to generate sprite for {film.file_id}: {e}')
            return False

    def create_text_thumbnail(self, title, timestamp, subtitle="", color_index=0, width=160, height=90):
        """Create a text-based thumbnail image for sprite frames"""
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
                    title_font = ImageFont.truetype(font_path, 12)  # Smaller font for sprite
                    time_font = ImageFont.truetype(font_path, 14)
                    subtitle_font = ImageFont.truetype(font_path, 10)
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
        timestamp_text = str(timestamp)
        if hasattr(time_font, 'getbbox'):
            bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
            time_width = bbox[2] - bbox[0]
        else:
            time_width, _ = draw.textsize(timestamp_text, font=time_font)
        time_x = (width - time_width) // 2
        draw.text((time_x, 5), timestamp_text, fill='white', font=time_font)
        
        # Draw subtitle if provided
        if subtitle:
            if hasattr(subtitle_font, 'getbbox'):
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
            else:
                subtitle_width, _ = draw.textsize(subtitle, font=subtitle_font)
            subtitle_x = (width - subtitle_width) // 2
            draw.text((subtitle_x, 25), subtitle, fill='white', font=subtitle_font)
        
        # Wrap and draw title text (more aggressively wrapped for small size)
        wrapped_text = textwrap.fill(title, width=15)
        lines = wrapped_text.split('\n')
        
        # Limit to 2-3 lines for sprite frames
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:12] + '...' if len(lines[2]) > 12 else lines[2]
        
        # Calculate starting Y position to center the text block
        line_height = 12
        text_block_height = len(lines) * line_height
        start_y = (height - text_block_height) // 2 + 10
        
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
            shadow_offset = 1
            draw.text((text_x + shadow_offset, text_y + shadow_offset), line, 
                     fill='black', font=title_font)
            draw.text((text_x, text_y), line, fill='white', font=title_font)
        
        return img

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