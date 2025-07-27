#!/usr/bin/env python3
"""
Comprehensive Thumbnail Management Tool

This script consolidates all thumbnail-related functionality:
- Generate sprite sheets for films with placeholder or real YouTube thumbnails
- Create individual chapter thumbnails
- Verify thumbnail existence and dimensions
- Analyze thumbnail coverage and issues
- Optimize thumbnails for size and quality
"""

import django
import os
import sys
import argparse
import shutil
import requests
import json
import re
from PIL import Image, ImageDraw, ImageFont

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter

def create_placeholder_sprite_for_film(film):
    """Create placeholder sprite with chapter information for a single film"""
    
    chapters = film.chapters.all().order_by('order')
    
    if not chapters.exists():
        print(f"    ⚠️ No chapters found, skipping")
        return False
    
    print(f"    Creating placeholder sprite for {chapters.count()} chapters...")
    
    # Color scheme for different chapter types
    chapter_colors = [
        (65, 105, 225),   # Royal Blue
        (34, 139, 34),    # Forest Green  
        (220, 20, 60),    # Crimson
        (255, 140, 0),    # Dark Orange
        (138, 43, 226),   # Blue Violet
        (0, 139, 139),    # Dark Cyan
        (255, 20, 147),   # Deep Pink
        (30, 144, 255),   # Dodger Blue
        (255, 165, 0),    # Orange
        (50, 205, 50),    # Lime Green
    ]
    
    # Create sprite with chapter information
    frame_width, frame_height = 160, 90
    sprite_width = frame_width * chapters.count()
    sprite_height = frame_height
    
    sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
    
    for i, chapter in enumerate(chapters):
        # Create frame image
        frame_image = Image.new('RGB', (frame_width, frame_height), chapter_colors[i % len(chapter_colors)])
        draw = ImageDraw.Draw(frame_image)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            time_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw timestamp prominently at top
        timestamp_text = chapter.start_time
        time_bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (frame_width - time_width) // 2
        
        # Background for timestamp
        draw.rectangle([time_x-3, 3, time_x+time_width+3, 23], fill=(0, 0, 0, 200))
        draw.text((time_x, 5), timestamp_text, fill=(255, 255, 255), font=time_font)
        
        # Draw chapter number
        chapter_num = f"Ch. {i+1}"
        draw.text((5, 25), chapter_num, fill=(255, 255, 255), font=title_font)
        
        # Draw chapter title (wrapped)
        title_words = chapter.title.split()
        title_lines = []
        current_line = []
        
        for word in title_words:
            test_line = ' '.join(current_line + [word])
            test_bbox = draw.textbbox((0, 0), test_line, font=small_font)
            test_width = test_bbox[2] - test_bbox[0]
            
            if test_width <= frame_width - 10:
                current_line.append(word)
            else:
                if current_line:
                    title_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    title_lines.append(word)
        
        if current_line:
            title_lines.append(' '.join(current_line))
        
        # Draw title lines (max 4 lines)
        y_offset = 45
        for line in title_lines[:4]:
            if y_offset < frame_height - 15:
                draw.text((5, y_offset), line, fill=(255, 255, 255), font=small_font)
                y_offset += 12
        
        # Add border
        draw.rectangle([0, 0, frame_width-1, frame_height-1], outline=(255, 255, 255), width=2)
        
        # Paste into sprite
        x_offset = i * frame_width
        sprite_image.paste(frame_image, (x_offset, 0))
    
    return sprite_image, frame_width, frame_height, chapters.count()

def create_youtube_sprite_for_film(film):
    """Create sprite using real YouTube thumbnails for a single film"""
    
    chapters = film.chapters.all().order_by('order')
    
    if not chapters.exists():
        print(f"    ⚠️ No chapters found, skipping")
        return False
    
    if film.youtube_id.startswith('placeholder_'):
        print(f"    ⚠️ Film has placeholder YouTube ID, using placeholder sprite")
        return create_placeholder_sprite_for_film(film)
    
    print(f"    Creating YouTube sprite for {chapters.count()} chapters...")
    
    frame_width, frame_height = 160, 90
    sprite_width = frame_width * chapters.count()
    sprite_height = frame_height
    
    sprite_image = Image.new('RGB', (sprite_width, sprite_height), (0, 0, 0))
    
    # YouTube thumbnail sources to try
    youtube_sources = ['1.jpg', '2.jpg', '3.jpg', 'hqdefault.jpg', 'mqdefault.jpg', 'default.jpg']
    
    for i, chapter in enumerate(chapters):
        frame_image = None
        
        # Try to download a YouTube thumbnail
        for source in youtube_sources:
            try:
                thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/{source}"
                response = requests.get(thumbnail_url, timeout=10)
                
                if response.status_code == 200:
                    # Load the image
                    from io import BytesIO
                    img = Image.open(BytesIO(response.content))
                    
                    # Resize to frame size
                    img = img.resize((frame_width, frame_height), Image.Resampling.LANCZOS)
                    
                    # Enhance brightness/contrast slightly to reduce ABAC patterns
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(1.1)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.1)
                    
                    frame_image = img
                    print(f"      ✓ Downloaded thumbnail from {source}")
                    break
                    
            except Exception as e:
                print(f"      ⚠️ Failed to download {source}: {e}")
                continue
        
        # If no thumbnail downloaded, create placeholder
        if frame_image is None:
            print(f"      📝 Creating placeholder for chapter {i+1}")
            frame_image = Image.new('RGB', (frame_width, frame_height), (65, 105, 225))
        
        # Add timestamp overlay
        draw = ImageDraw.Draw(frame_image)
        
        # Load font for timestamp
        try:
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            time_font = ImageFont.load_default()
        
        # Draw timestamp
        timestamp_text = chapter.start_time
        time_bbox = draw.textbbox((0, 0), timestamp_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (frame_width - time_width) // 2
        
        # Background for timestamp
        draw.rectangle([time_x-3, 3, time_x+time_width+3, 23], fill=(0, 0, 0, 180))
        draw.text((time_x, 5), timestamp_text, fill=(255, 255, 255), font=time_font)
        
        # Add chapter number in bottom corner
        chapter_num = f"Ch. {i+1}"
        draw.text((5, frame_height-20), chapter_num, fill=(255, 255, 255), font=time_font)
        
        # Paste into sprite
        x_offset = i * frame_width
        sprite_image.paste(frame_image, (x_offset, 0))
    
    return sprite_image, frame_width, frame_height, chapters.count()

def save_sprite(film, sprite_image, frame_width, frame_height, frame_count, backup=True):
    """Save sprite image and update film metadata"""
    
    # Ensure directories exist
    previews_dir = '/home/viblio/family_films/static/thumbnails/previews'
    os.makedirs(previews_dir, exist_ok=True)
    
    sprite_path = os.path.join(previews_dir, f'{film.file_id}_sprite.jpg')
    
    # Backup existing sprite if it exists
    if backup and os.path.exists(sprite_path):
        backup_path = sprite_path.replace('.jpg', '_backup.jpg')
        shutil.copy2(sprite_path, backup_path)
        print(f"      📦 Backed up existing sprite")
    
    sprite_image.save(sprite_path, 'JPEG', quality=90)
    sprite_image.close()
    
    print(f"      ✅ Created sprite: {os.path.getsize(sprite_path):,} bytes")
    
    # Update film sprite metadata
    film.preview_sprite_width = frame_width
    film.preview_sprite_height = frame_height
    film.preview_frame_count = frame_count
    film.preview_sprite_url = f"/static/thumbnails/previews/{film.file_id}_sprite.jpg"
    film.save()
    
    return True

def create_chapter_thumbnails_for_film(film, use_youtube=True):
    """Create individual chapter thumbnails for a film"""
    
    chapters = film.chapters.all().order_by('order')
    
    if not chapters.exists():
        print(f"    ⚠️ No chapters found, skipping")
        return 0
    
    print(f"    Creating chapter thumbnails for {chapters.count()} chapters...")
    
    # Ensure directories exist
    chapters_dir = '/home/viblio/family_films/static/thumbnails/chapters'
    os.makedirs(chapters_dir, exist_ok=True)
    
    thumbnail_size = (80, 60)
    created_count = 0
    
    for chapter in chapters:
        chapter_image = None
        
        # Try to get YouTube thumbnail if enabled and available
        if use_youtube and not film.youtube_id.startswith('placeholder_'):
            try:
                thumbnail_url = f"https://img.youtube.com/vi/{film.youtube_id}/hqdefault.jpg"
                response = requests.get(thumbnail_url, timeout=10)
                
                if response.status_code == 200:
                    from io import BytesIO
                    chapter_image = Image.open(BytesIO(response.content))
                    chapter_image = chapter_image.resize(thumbnail_size, Image.Resampling.LANCZOS)
                    
            except Exception as e:
                print(f"      ⚠️ Failed to download YouTube thumbnail: {e}")
        
        # Create placeholder if no YouTube thumbnail
        if chapter_image is None:
            chapter_image = Image.new('RGB', thumbnail_size, (65, 105, 225))
            draw = ImageDraw.Draw(chapter_image)
            
            # Add timestamp
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            timestamp_text = chapter.start_time
            time_bbox = draw.textbbox((0, 0), timestamp_text, font=font)
            time_width = time_bbox[2] - time_bbox[0]
            time_x = (thumbnail_size[0] - time_width) // 2
            
            draw.text((time_x, 5), timestamp_text, fill=(255, 255, 255), font=font)
        
        # Save chapter thumbnail
        chapter_path = os.path.join(chapters_dir, f'{film.file_id}_{chapter.id}.jpg')
        chapter_image.save(chapter_path, 'JPEG', quality=85)
        chapter_image.close()
        
        # Update chapter thumbnail URL
        chapter.thumbnail_url = f"/static/thumbnails/chapters/{film.file_id}_{chapter.id}.jpg"
        chapter.save()
        
        created_count += 1
    
    print(f"      ✅ Created {created_count} chapter thumbnails")
    return created_count

def verify_thumbnails(film_ids=None):
    """Verify thumbnail existence and dimensions"""
    print("=== Verifying Thumbnails ===\n")
    
    if film_ids:
        films = Film.objects.filter(file_id__in=film_ids)
    else:
        films = Film.objects.filter(chapters__isnull=False).distinct()
    
    total_films = films.count()
    verified_sprites = 0
    missing_sprites = 0
    dimension_mismatches = 0
    
    for film in films:
        sprite_path = f'/home/viblio/family_films/static/thumbnails/previews/{film.file_id}_sprite.jpg'
        
        if os.path.exists(sprite_path):
            verified_sprites += 1
            
            # Check dimensions
            try:
                with Image.open(sprite_path) as img:
                    actual_width, actual_height = img.size
                    chapter_count = film.chapters.count()
                    expected_width = film.preview_sprite_width * chapter_count if film.preview_sprite_width else 160 * chapter_count
                    
                    if actual_width != expected_width or actual_height != film.preview_sprite_height:
                        print(f"  ❌ {film.file_id}: Dimension mismatch - actual: {actual_width}x{actual_height}, expected: {expected_width}x{film.preview_sprite_height}")
                        dimension_mismatches += 1
                    else:
                        print(f"  ✅ {film.file_id}: OK ({actual_width}x{actual_height})")
                        
            except Exception as e:
                print(f"  ⚠️ {film.file_id}: Error checking dimensions: {e}")
        else:
            missing_sprites += 1
            print(f"  ❌ {film.file_id}: Sprite missing")
    
    print(f"\n=== Verification Summary ===")
    print(f"Total films: {total_films}")
    print(f"✅ Verified sprites: {verified_sprites}")
    print(f"❌ Missing sprites: {missing_sprites}")
    print(f"⚠️ Dimension mismatches: {dimension_mismatches}")

def extract_storyboard_data(video_id):
    """Extract YouTube storyboard data for a video (basic implementation)"""
    print(f"=== Extracting Storyboard Data for {video_id} ===\n")
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.text
        
        # Look for storyboard data in the page
        storyboard_pattern = r'"playerStoryboardSpecRenderer":\s*{"spec":"([^"]+)"'
        match = re.search(storyboard_pattern, content)
        
        if match:
            storyboard_url_template = match.group(1)
            print(f"✅ Found storyboard template: {storyboard_url_template[:100]}...")
            
            # Basic storyboard info extraction
            if 'storyboard3_L' in storyboard_url_template:
                print("📊 Level-based storyboard detected")
                print("ℹ️  This contains multiple quality levels of timeline thumbnails")
            else:
                print("📊 Standard storyboard detected")
            
            return {
                'template': storyboard_url_template,
                'available': True,
                'type': 'level-based' if 'storyboard3_L' in storyboard_url_template else 'standard'
            }
        else:
            print("❌ No storyboard data found in page")
            return {'available': False}
            
    except Exception as e:
        print(f"❌ Error extracting storyboard data: {str(e)}")
        return {'available': False, 'error': str(e)}

def analyze_thumbnail_coverage():
    """Analyze overall thumbnail coverage and issues"""
    print("=== Thumbnail Coverage Analysis ===\n")
    
    total_films = Film.objects.count()
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct().count()
    
    # Check sprite coverage
    previews_dir = '/home/viblio/family_films/static/thumbnails/previews'
    sprite_files = []
    if os.path.exists(previews_dir):
        sprite_files = [f for f in os.listdir(previews_dir) if f.endswith('_sprite.jpg')]
    
    # Check chapter thumbnail coverage
    chapters_dir = '/home/viblio/family_films/static/thumbnails/chapters'
    chapter_files = []
    if os.path.exists(chapters_dir):
        chapter_files = [f for f in os.listdir(chapters_dir) if f.endswith('.jpg')]
    
    print(f"Films in database: {total_films}")
    print(f"Films with chapters: {films_with_chapters}")
    print(f"Sprite files found: {len(sprite_files)}")
    print(f"Chapter thumbnail files found: {len(chapter_files)}")
    
    # Coverage percentage
    if films_with_chapters > 0:
        sprite_coverage = (len(sprite_files) / films_with_chapters) * 100
        print(f"\nSprite coverage: {sprite_coverage:.1f}%")
    
    # Find films missing sprites
    films_missing_sprites = []
    for film in Film.objects.filter(chapters__isnull=False).distinct():
        sprite_path = os.path.join(previews_dir, f'{film.file_id}_sprite.jpg')
        if not os.path.exists(sprite_path):
            films_missing_sprites.append(film.file_id)
    
    if films_missing_sprites:
        print(f"\nFilms missing sprites: {len(films_missing_sprites)}")
        for file_id in films_missing_sprites[:10]:  # Show first 10
            print(f"  - {file_id}")
        if len(films_missing_sprites) > 10:
            print(f"  ... and {len(films_missing_sprites) - 10} more")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive thumbnail management tool')
    parser.add_argument('command', choices=['create-sprites', 'create-chapters', 'verify', 
                                           'analyze', 'storyboard', 'all'],
                        help='Command to run')
    parser.add_argument('--film-ids', nargs='+', help='Specific film IDs to process')
    parser.add_argument('--use-youtube', action='store_true', default=True,
                        help='Use real YouTube thumbnails when available')
    parser.add_argument('--placeholder-only', action='store_true',
                        help='Create placeholder sprites only (no YouTube downloads)')
    parser.add_argument('--no-backup', action='store_true',
                        help='Do not backup existing sprites')
    
    args = parser.parse_args()
    
    if args.command == 'create-sprites':
        print("=== Creating Sprite Sheets ===\n")
        
        if args.film_ids:
            films = Film.objects.filter(file_id__in=args.film_ids, chapters__isnull=False).distinct()
        else:
            films = Film.objects.filter(chapters__isnull=False).distinct()
        
        use_youtube = args.use_youtube and not args.placeholder_only
        backup = not args.no_backup
        
        success_count = 0
        for i, film in enumerate(films, 1):
            print(f"[{i}/{films.count()}] {film.file_id}: {film.title[:50]}...")
            
            try:
                if use_youtube:
                    sprite_data = create_youtube_sprite_for_film(film)
                else:
                    sprite_data = create_placeholder_sprite_for_film(film)
                
                if sprite_data and len(sprite_data) == 4:
                    sprite_image, frame_width, frame_height, frame_count = sprite_data
                    if save_sprite(film, sprite_image, frame_width, frame_height, frame_count, backup):
                        success_count += 1
                        
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print(f"\n✅ Created {success_count} sprites")
        
    elif args.command == 'create-chapters':
        print("=== Creating Chapter Thumbnails ===\n")
        
        if args.film_ids:
            films = Film.objects.filter(file_id__in=args.film_ids, chapters__isnull=False).distinct()
        else:
            films = Film.objects.filter(chapters__isnull=False).distinct()
        
        use_youtube = args.use_youtube and not args.placeholder_only
        
        total_thumbnails = 0
        for i, film in enumerate(films, 1):
            print(f"[{i}/{films.count()}] {film.file_id}: {film.title[:50]}...")
            
            try:
                count = create_chapter_thumbnails_for_film(film, use_youtube)
                total_thumbnails += count
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print(f"\n✅ Created {total_thumbnails} chapter thumbnails")
        
    elif args.command == 'verify':
        verify_thumbnails(args.film_ids)
        
    elif args.command == 'analyze':
        analyze_thumbnail_coverage()
        
    elif args.command == 'storyboard':
        if args.film_ids:
            for film_id in args.film_ids:
                try:
                    film = Film.objects.get(file_id=film_id)
                    if not film.youtube_id.startswith('placeholder_'):
                        extract_storyboard_data(film.youtube_id)
                    else:
                        print(f"Film {film_id} has placeholder YouTube ID")
                except Film.DoesNotExist:
                    print(f"Film {film_id} not found")
                print()
        else:
            print("ERROR: --film-ids required for storyboard command")
        
    elif args.command == 'all':
        print("Running all thumbnail operations...\n")
        
        # Create sprites
        print("=== Creating Sprite Sheets ===\n")
        films = Film.objects.filter(chapters__isnull=False).distinct()
        use_youtube = args.use_youtube and not args.placeholder_only
        
        for i, film in enumerate(films, 1):
            print(f"[{i}/{films.count()}] {film.file_id}: Creating sprite...")
            
            try:
                if use_youtube:
                    sprite_data = create_youtube_sprite_for_film(film)
                else:
                    sprite_data = create_placeholder_sprite_for_film(film)
                
                if sprite_data and len(sprite_data) == 4:
                    sprite_image, frame_width, frame_height, frame_count = sprite_data
                    save_sprite(film, sprite_image, frame_width, frame_height, frame_count, not args.no_backup)
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print("\n" + "="*60 + "\n")
        
        # Create chapter thumbnails
        print("=== Creating Chapter Thumbnails ===\n")
        
        for i, film in enumerate(films, 1):
            print(f"[{i}/{films.count()}] {film.file_id}: Creating chapter thumbnails...")
            
            try:
                create_chapter_thumbnails_for_film(film, use_youtube)
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        print("\n" + "="*60 + "\n")
        
        # Verify results
        verify_thumbnails()
        
        print("\n" + "="*60 + "\n")
        
        # Analyze coverage
        analyze_thumbnail_coverage()

if __name__ == '__main__':
    main()