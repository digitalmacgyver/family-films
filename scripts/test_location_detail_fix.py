#!/usr/bin/env python
"""
Test the location detail view fix.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Location, Film
from django.db.models import Q

def test_location_detail_fix():
    # Test with a chapter-only location
    location = Location.objects.filter(name='Grand Canyon Arizona').first()
    if location:
        print(f'Testing location detail for: "{location.name}"')
        
        # Old query (direct associations only)
        old_films = Film.objects.filter(locations=location).exclude(youtube_id__startswith='placeholder_')
        print(f'Old query would show: {old_films.count()} films')
        
        # New query (direct + chapter associations)
        new_films = Film.objects.filter(
            Q(locations=location) | Q(chapters__locations=location)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        print(f'New query shows: {new_films.count()} films')
        
        for film in new_films:
            print(f'  - {film.title}')
    else:
        print('Location not found')

if __name__ == "__main__":
    test_location_detail_fix()