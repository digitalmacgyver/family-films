#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Chapter

def analyze_thumbnail_issues():
    """Analyze the thumbnail generation issues"""
    
    print("=== Analyzing Thumbnail Issues ===\n")
    
    # 1. Check P-61_FROS chapters directory issue
    print("1. CHECKING P-61_FROS CHAPTER THUMBNAILS")
    print("-" * 50)
    
    try:
        film_p61 = Film.objects.get(file_id='P-61_FROS')
        print(f"Film: {film_p61.title}")
        chapters_p61 = film_p61.chapters.all().order_by('order')
        print(f"Number of chapters: {chapters_p61.count()}")
        
        # Check for chapter thumbnail files
        chapter_thumbs_dir = '/home/viblio/family_films/static/thumbnails/chapters'
        if os.path.exists(chapter_thumbs_dir):
            files = [f for f in os.listdir(chapter_thumbs_dir) if f.startswith('P-61_FROS')]
            print(f"Chapter thumbnail files found: {len(files)}")
            for f in files[:5]:  # Show first 5
                print(f"  - {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
        else:
            print("Chapter thumbnails directory does not exist")
            
    except Film.DoesNotExist:
        print("Film P-61_FROS not found")
    
    print()
    
    # 2. Check PA-03_FROS sprite vs chapters mismatch
    print("2. CHECKING PA-03_FROS SPRITE VS CHAPTERS MISMATCH")
    print("-" * 50)
    
    try:
        film_pa03 = Film.objects.get(file_id='PA-03_FROS')
        print(f"Film: {film_pa03.title}")
        chapters_pa03 = film_pa03.chapters.all().order_by('order')
        print(f"Number of chapters: {chapters_pa03.count()}")
        
        print(f"\nChapter details:")
        for i, chapter in enumerate(chapters_pa03[:5]):  # Show first 5 chapters
            print(f"  {i+1}. {chapter.start_time} - {chapter.title}")
        if chapters_pa03.count() > 5:
            print(f"  ... and {chapters_pa03.count() - 5} more chapters")
            
        print(f"\nAnimated thumbnail info:")
        print(f"  Sprite URL: {film_pa03.preview_sprite_url}")
        print(f"  Frame count: {film_pa03.preview_frame_count}")
        print(f"  Frame interval: {film_pa03.preview_frame_interval}")
        print(f"  Expected frames for {chapters_pa03.count()} chapters: {chapters_pa03.count()}")
        print(f"  Actual frames in sprite: {film_pa03.preview_frame_count}")
        print(f"  Mismatch: {'YES' if film_pa03.preview_frame_count != chapters_pa03.count() else 'NO'}")
        
    except Film.DoesNotExist:
        print("Film PA-03_FROS not found")
    
    print()
    
    # 3. General analysis of all films
    print("3. GENERAL ANALYSIS OF ALL FILMS")
    print("-" * 50)
    
    films_with_sprites = Film.objects.filter(preview_sprite_url__isnull=False).exclude(preview_sprite_url='')
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct()
    
    print(f"Total films: {Film.objects.count()}")
    print(f"Films with sprite thumbnails: {films_with_sprites.count()}")
    print(f"Films with chapters: {films_with_chapters.count()}")
    
    # Check for mismatches
    print(f"\nMismatch analysis:")
    mismatches = []
    for film in films_with_sprites:
        chapter_count = film.chapters.count()
        sprite_frames = film.preview_frame_count or 0
        if chapter_count > 0 and sprite_frames != chapter_count:
            mismatches.append({
                'file_id': film.file_id,
                'title': film.title,
                'chapters': chapter_count,
                'sprite_frames': sprite_frames
            })
    
    print(f"Films with chapter/sprite mismatches: {len(mismatches)}")
    for mismatch in mismatches[:10]:  # Show first 10
        print(f"  - {mismatch['file_id']}: {mismatch['chapters']} chapters, {mismatch['sprite_frames']} frames")
    
    if len(mismatches) > 10:
        print(f"  ... and {len(mismatches) - 10} more")
    
    print()
    
    # 4. Check thumbnail generation script
    print("4. CHECKING THUMBNAIL GENERATION SCRIPT")
    print("-" * 50)
    
    script_path = '/home/viblio/family_films/main/management/commands/generate_chapter_thumbnails.py'
    if os.path.exists(script_path):
        print(f"✓ Thumbnail generation script exists: {script_path}")
        
        # Get file size and modification time
        stat = os.stat(script_path)
        print(f"  Size: {stat.st_size} bytes")
        print(f"  Last modified: {stat.st_mtime}")
    else:
        print(f"✗ Thumbnail generation script not found: {script_path}")
    
    print(f"\n=== SUMMARY OF ISSUES ===")
    print(f"1. P-61_FROS has old chapter thumbnails (pre-sprite system)")
    print(f"2. Sprite frames don't match chapter counts for many films")
    print(f"3. Need to regenerate thumbnails with proper chapter alignment")
    print(f"4. Sprite generation may have ABAC pattern issue (repeated frames)")

if __name__ == '__main__':
    analyze_thumbnail_issues()