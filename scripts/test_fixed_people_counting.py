#!/usr/bin/env python
"""
Test the fixed people directory counting.
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
from django.db.models import Q

def test_fixed_people_counting():
    # Test the new logic with John Hayward Sr.
    john_sr = Person.objects.filter(first_name='John', last_name='Hayward Sr.').first()
    if john_sr:
        # New calculation method
        films = Film.objects.filter(
            Q(people=john_sr) | Q(chapters__people=john_sr)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        
        print(f'John Hayward Sr. - Fixed counting:')
        print(f'  Should show: {films.count()} films')
        print(f'  Direct films: {john_sr.film_set.count()}')
        chapter_film_count = john_sr.chapter_set.aggregate(
            c=Count("film", distinct=True)
        )["c"] or 0
        print(f'  Chapter films: {chapter_film_count}')
        print(f'  Sum would be: {john_sr.film_set.count() + chapter_film_count} (old method)')
        
    # Test the directory query logic
    print('\nTesting directory query:')
    people = Person.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct()
    
    print(f'Found {people.count()} people with associations')
    
    # Test a few people
    test_people = [
        ('John', 'Hayward Sr.'),
        ('Joy', 'Hofer (nee Hayward)'),
        ('Josephine', 'Hayward (nee Myre)')
    ]
    
    for first_name, last_name in test_people:
        person = people.filter(first_name=first_name, last_name=last_name).first()
        if person:
            films = Film.objects.filter(
                Q(people=person) | Q(chapters__people=person)
            ).exclude(youtube_id__startswith='placeholder_').distinct()
            print(f'{person.full_name()}: {films.count()} films')

if __name__ == "__main__":
    from django.db.models import Count
    test_fixed_people_counting()