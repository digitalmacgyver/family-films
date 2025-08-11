#!/usr/bin/env python3
"""
Fix Chapter Thumbnail URLs

Updates chapter thumbnail URLs to include the proper /static/ prefix
so Django can serve them correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Chapter

def fix_thumbnail_urls():
    """Fix all chapter thumbnail URLs to include /static/ prefix"""
    print("=== FIXING CHAPTER THUMBNAIL URLS ===\n")
    
    # Get all chapters with thumbnail URLs
    chapters = Chapter.objects.exclude(thumbnail_url='').exclude(thumbnail_url__isnull=True)
    
    print(f"Found {chapters.count()} chapters with thumbnails")
    
    updated_count = 0
    
    for chapter in chapters:
        old_url = chapter.thumbnail_url
        
        # Skip if already has /static/ prefix
        if old_url.startswith('/static/'):
            continue
            
        # Add /static/ prefix to the URL
        new_url = f"/static{old_url}"
        
        # Update the chapter
        chapter.thumbnail_url = new_url
        chapter.save()
        
        print(f"Updated {chapter.film.file_id} - {chapter.title}")
        print(f"  Old: {old_url}")
        print(f"  New: {new_url}")
        
        updated_count += 1
    
    print(f"\n✅ Updated {updated_count} chapter thumbnail URLs")

if __name__ == "__main__":
    fix_thumbnail_urls()