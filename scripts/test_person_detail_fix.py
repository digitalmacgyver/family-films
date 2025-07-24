#!/usr/bin/env python
"""
Test the person detail view fix.
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

def test_person_detail_fix():
    # Test the person detail view query
    person = Person.objects.filter(first_name='their', last_name__icontains='various children').first()
    if person:
        print(f'Testing person detail for: "{person.full_name()}"')
        
        # Old query (direct associations only)
        old_films = Film.objects.filter(people=person).exclude(youtube_id__startswith='placeholder_')
        print(f'Old query would show: {old_films.count()} films')
        
        # New query (direct + chapter associations)
        new_films = Film.objects.filter(
            Q(people=person) | Q(chapters__people=person)
        ).exclude(youtube_id__startswith='placeholder_').distinct()
        print(f'New query shows: {new_films.count()} films')
        
        for film in new_films:
            print(f'  - {film.title}')
    else:
        print('Person not found')

if __name__ == "__main__":
    test_person_detail_fix()