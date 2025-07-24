#!/usr/bin/env python
"""
Analyze the locations directory issue to see how many locations are missing.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Location
from django.db.models import Count, Q

def analyze_locations_directory():
    print('=== Locations Association Analysis ===')
    
    only_films = Location.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count__gt=0, chapter_count=0).count()

    only_chapters = Location.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count=0, chapter_count__gt=0).count()

    both = Location.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count__gt=0, chapter_count__gt=0).count()

    total_with_associations = Location.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(Q(film_count__gt=0) | Q(chapter_count__gt=0)).count()

    print(f'Locations only associated with films: {only_films}')
    print(f'Locations only associated with chapters: {only_chapters}')
    print(f'Locations associated with both: {both}')  
    print(f'Total locations with any associations: {total_with_associations}')

    print('\n=== Current Locations Directory Query Results ===')
    current_query_count = Location.objects.annotate(
        film_count=Count('film')
    ).filter(film_count__gt=0).count()
    print(f'Current directory shows: {current_query_count} locations')

    print('\n=== Proposed Fixed Query Results ===')
    fixed_query_count = Location.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0).count()
    print(f'Fixed directory would show: {fixed_query_count} locations')
    print(f'Missing locations: {fixed_query_count - current_query_count}')

    # Show some examples of missing locations
    if fixed_query_count > current_query_count:
        print('\n=== Examples of Missing Locations (Chapter-only) ===')
        missing_locations = Location.objects.annotate(
            film_count=Count('film'),
            chapter_count=Count('chapter')
        ).filter(film_count=0, chapter_count__gt=0)[:10]
        
        for location in missing_locations:
            print(f'- "{location.name}": {location.chapter_count} chapters')
    else:
        print('\n=== No missing locations found ===')

if __name__ == "__main__":
    analyze_locations_directory()