#!/usr/bin/env python
"""
Test people directory counting for double-counting issues.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, Film
from django.db.models import Count, Q

def test_people_counting():
    # Test John Hayward Sr. - likely to have both direct and chapter associations
    john_sr = Person.objects.filter(first_name='John', last_name='Hayward Sr.').first()
    if john_sr:
        # Current annotation
        annotated = Person.objects.filter(pk=john_sr.pk).annotate(
            film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
        ).first()
        
        # Actual unique films
        unique_films = Film.objects.filter(
            Q(people=john_sr) | Q(chapters__people=john_sr)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        
        print(f'John Hayward Sr.:')
        print(f'  Directory shows: {annotated.film_count}')
        print(f'  Actual unique films: {unique_films.count()}')
        print(f'  Direct films: {john_sr.film_set.count()}')
        chapter_film_count = john_sr.chapter_set.aggregate(c=Count("film", distinct=True))["c"] or 0
        print(f'  Chapter films: {chapter_film_count}')
        
        if annotated.film_count != unique_films.count():
            print(f'  ❌ DOUBLE-COUNTING DETECTED: {annotated.film_count} vs {unique_films.count()}')
        else:
            print(f'  ✅ Counts match correctly')

if __name__ == "__main__":
    test_people_counting()