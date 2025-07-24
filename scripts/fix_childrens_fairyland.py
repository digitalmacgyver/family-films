#!/usr/bin/env python
"""
Fix the Children's Fairyland location to split it into proper locations.
The CSV had a typo (Fairlyand vs Fairyland) so we handle this manually.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Location, Film, Chapter, FilmLocations, ChapterLocations
from django.db import transaction

def fix_childrens_fairyland():
    """Fix the Children's Fairyland location."""
    
    # Find the original location
    original_location = Location.objects.filter(name="California locations: Children's Fairyland park in Oakland").first()
    
    if not original_location:
        print("Original location not found!")
        return
    
    print(f"Found original location: {original_location.name}")
    print(f"Films: {original_location.film_set.count()}, Chapters: {original_location.chapter_set.count()}")
    
    # Create or get the new locations
    new_locations = [
        "Children's Fairyland Park",
        "Oakland", 
        "California"
    ]
    
    with transaction.atomic():
        location_objects = []
        for loc_name in new_locations:
            loc_obj = Location.objects.filter(name__iexact=loc_name).first()
            if not loc_obj:
                loc_obj = Location.objects.create(name=loc_name)
                print(f"Created new location: {loc_name}")
            else:
                print(f"Using existing location: {loc_name}")
            location_objects.append(loc_obj)
        
        # Update films
        for film in original_location.film_set.all():
            print(f"Updating film: {film.title}")
            for new_loc in location_objects:
                film_location, created = FilmLocations.objects.get_or_create(
                    film=film, location=new_loc
                )
                if created:
                    print(f"  + Added location: {new_loc.name}")
                else:
                    print(f"  = Already has location: {new_loc.name}")
        
        # Update chapters  
        for chapter in original_location.chapter_set.all():
            print(f"Updating chapter: {chapter.title}")
            for new_loc in location_objects:
                chapter_location, created = ChapterLocations.objects.get_or_create(
                    chapter=chapter, location=new_loc
                )
                if created:
                    print(f"  + Added location: {new_loc.name}")
                else:
                    print(f"  = Already has location: {new_loc.name}")
        
        # Remove the original location associations and delete it
        FilmLocations.objects.filter(location=original_location).delete()
        ChapterLocations.objects.filter(location=original_location).delete()
        original_location.delete()
        print(f"Removed original location: California locations: Children's Fairyland park in Oakland")
    
    print("Fix complete!")

if __name__ == "__main__":
    fix_childrens_fairyland()