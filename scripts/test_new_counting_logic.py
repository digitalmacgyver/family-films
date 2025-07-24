#!/usr/bin/env python
"""
Test the new counting logic for locations.
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

def test_new_counting_logic():
    # Test the new logic with Anaheim
    anaheim = Location.objects.filter(name='Anaheim').first()
    if anaheim:
        films = Film.objects.filter(
            Q(locations=anaheim) | Q(chapters__locations=anaheim)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        
        print(f'Anaheim should show: {films.count()} films')
        for film in films:
            print(f'  - {film.title}')
    
    # Test the directory query
    print('\nTesting directory query:')
    locations = Location.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct().order_by('name')
    
    print(f'Found {locations.count()} locations with associations')
    
    # Test a few locations
    test_locations = ['Anaheim', 'California', 'Michigan']
    for loc_name in test_locations:
        location = locations.filter(name=loc_name).first()
        if location:
            films = Film.objects.filter(
                Q(locations=location) | Q(chapters__locations=location)
            ).exclude(youtube_id__startswith='placeholder_').distinct()
            print(f'{loc_name}: {films.count()} films')

if __name__ == "__main__":
    test_new_counting_logic()