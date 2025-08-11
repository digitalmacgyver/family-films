#!/usr/bin/env python3
"""
Check Animated Thumbnail Status for Batch D Films

Verify that the Batch D films now have animated thumbnails after
extracting chapter thumbnails.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Film

def check_animated_thumbnails():
    """Check animated thumbnail status for Batch D films"""
    print("=== CHECKING ANIMATED THUMBNAIL STATUS FOR BATCH D FILMS ===\n")
    
    # Get films that have chapters (likely Batch D)
    films_with_chapters = Film.objects.filter(chapters__isnull=False).distinct()
    
    total_films = 0
    films_with_animation = 0
    films_with_chapters_thumbs = 0
    
    print(f"Films with animated thumbnails:")
    print("-" * 80)
    
    for film in films_with_chapters.order_by('file_id'):
        total_films += 1
        
        # Check if has animated thumbnails
        has_animated = film.has_animated_thumbnail()
        has_chapter_thumbs = film.has_chapter_thumbnails()
        chapter_count = film.chapters.count()
        thumbnail_count = film.chapters.exclude(thumbnail_url__isnull=True).exclude(thumbnail_url__exact="").count()
        
        if has_animated:
            films_with_animation += 1
        
        if has_chapter_thumbs:
            films_with_chapters_thumbs += 1
        
        # Show status
        status = "✓ ANIMATED" if has_animated else "✗ No Animation"
        print(f"{film.file_id:<18} {status:<15} Chapters: {chapter_count:2d} Thumbnails: {thumbnail_count:2d}")
        
        # Show chapter thumbnail URLs for films with few thumbnails
        if thumbnail_count > 0 and thumbnail_count < 3:
            for chapter in film.chapters.filter(thumbnail_url__isnull=False).exclude(thumbnail_url__exact=""):
                print(f"                   Chapter {chapter.order}: {chapter.thumbnail_url}")
    
    print(f"\n" + "=" * 80)
    print(f"SUMMARY:")
    print(f"Total films with chapters: {total_films}")
    print(f"Films with animated thumbnails: {films_with_animation} ({films_with_animation/total_films*100:.1f}%)")
    print(f"Films with chapter-based animation: {films_with_chapters_thumbs} ({films_with_chapters_thumbs/total_films*100:.1f}%)")
    
    return films_with_animation

def main():
    animated_count = check_animated_thumbnails()
    print(f"\n🎬 Success! {animated_count} Batch D films now have animated thumbnails!")
    return 0

if __name__ == "__main__":
    sys.exit(main())