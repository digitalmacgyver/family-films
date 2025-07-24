#!/usr/bin/env python
"""
Analyze the Anaheim location discrepancy between directory count and detail page.
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
from django.db.models import Count, Q

def analyze_anaheim_location():
    # Find Anaheim location
    anaheim = Location.objects.filter(name='Anaheim').first()
    if not anaheim:
        print("Anaheim location not found")
        return
    
    print(f"Analyzing location: {anaheim.name} (ID: {anaheim.id})")
    
    # Directory query - what the directory page uses
    directory_count = Location.objects.filter(pk=anaheim.pk).annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).first().film_count
    print(f"Directory shows: {directory_count} films")
    
    # Direct film associations
    direct_films = Film.objects.filter(locations=anaheim).exclude(youtube_id__startswith='placeholder_')
    print(f"Direct film associations: {direct_films.count()}")
    for film in direct_films:
        print(f"  - {film.title}")
    
    # Chapter-based associations
    chapter_films = Film.objects.filter(chapters__locations=anaheim).exclude(youtube_id__startswith='placeholder_').distinct()
    print(f"Chapter-based associations: {chapter_films.count()}")
    for film in chapter_films:
        print(f"  - {film.title}")
    
    # All unique films (what detail page should show)
    all_films = Film.objects.filter(
        Q(locations=anaheim) | Q(chapters__locations=anaheim)
    ).exclude(youtube_id__startswith='placeholder_').distinct()
    print(f"All unique films (should show): {all_films.count()}")
    for film in all_films:
        print(f"  - {film.title}")
    
    # Current detail page query (what's actually shown)
    detail_films = Film.objects.filter(locations=anaheim).exclude(youtube_id__startswith='placeholder_')
    print(f"Current detail page shows: {detail_films.count()}")
    
    # Check for overlap
    direct_ids = set(direct_films.values_list('id', flat=True))
    chapter_ids = set(chapter_films.values_list('id', flat=True))
    overlap = direct_ids.intersection(chapter_ids)
    print(f"Films in both direct and chapter: {len(overlap)}")
    
    # Expected calculation
    unique_total = len(direct_ids.union(chapter_ids))
    print(f"Expected unique total: {unique_total}")

if __name__ == "__main__":
    analyze_anaheim_location()