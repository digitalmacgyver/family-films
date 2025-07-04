#!/usr/bin/env python3

import django
import os
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
sys.path.append('/home/viblio/family_films')
django.setup()

from main.models import Film, Tag

def test_tag_functionality():
    """Test tag functionality on film details page"""
    
    print("=== Testing Tag Functionality ===\n")
    
    # Get a film
    film = Film.objects.get(file_id='P-56_FROS')
    print(f"Film: {film.title}")
    
    # Current tags
    current_tags = list(film.tags.all())
    print(f"Current tags: {[t.tag for t in current_tags]}")
    
    # Add a test tag if not exists
    test_tag, created = Tag.objects.get_or_create(
        tag='TestTagForDeletion',
        defaults={'category': 'other', 'description': 'Test tag for deletion'}
    )
    
    if created:
        print(f"\nCreated new tag: {test_tag.tag}")
    
    # Add tag to film
    film.tags.add(test_tag)
    print(f"Added tag '{test_tag.tag}' to film")
    
    # Verify tags
    film_tags = list(film.tags.all())
    print(f"\nFilm now has tags: {[t.tag for t in film_tags]}")
    
    print("\n✅ Tag setup complete!")
    print(f"\nTo test:")
    print(f"1. Visit: http://localhost:8000/films/{film.file_id}/")
    print(f"2. Look for the tag '{test_tag.tag}' - it should be clickable")
    print(f"3. Click on the tag - it should go to search page")
    print(f"4. Login as admin")
    print(f"5. Click the 'x' on the tag - it should be deleted")

if __name__ == '__main__':
    test_tag_functionality()