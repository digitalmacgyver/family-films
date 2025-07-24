#!/usr/bin/env python
"""
Analyze the people directory issue to see how many people are missing.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person
from django.db.models import Count, Q

def analyze_people_directory():
    # Check the specific person mentioned
    person = Person.objects.filter(first_name='their', last_name__icontains='various children').first()
    if person:
        print(f'Found person: "{person.full_name()}"')
        print(f'Direct film associations: {person.film_set.count()}')
        print(f'Chapter associations: {person.chapter_set.count()}')
        if person.chapter_set.exists():
            chapters = person.chapter_set.all()
            for chapter in chapters:
                print(f'  - Chapter: {chapter.title} (Film: {chapter.film.title})')
    else:
        print('Person not found with that name pattern')

    print('\n=== People Association Analysis ===')
    only_films = Person.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count__gt=0, chapter_count=0).count()

    only_chapters = Person.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count=0, chapter_count__gt=0).count()

    both = Person.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count__gt=0, chapter_count__gt=0).count()

    total_with_associations = Person.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(Q(film_count__gt=0) | Q(chapter_count__gt=0)).count()

    print(f'People only associated with films: {only_films}')
    print(f'People only associated with chapters: {only_chapters}')
    print(f'People associated with both: {both}')  
    print(f'Total people with any associations: {total_with_associations}')

    print('\n=== Current People Directory Query Results ===')
    current_query_count = Person.objects.annotate(
        film_count=Count('film')
    ).filter(film_count__gt=0).count()
    print(f'Current directory shows: {current_query_count} people')

    print('\n=== Proposed Fixed Query Results ===')
    fixed_query_count = Person.objects.annotate(
        film_count=Count('film', distinct=True) + Count('chapter__film', distinct=True)
    ).filter(film_count__gt=0).count()
    print(f'Fixed directory would show: {fixed_query_count} people')
    print(f'Missing people: {fixed_query_count - current_query_count}')

    # Show some examples of missing people
    print('\n=== Examples of Missing People (Chapter-only) ===')
    missing_people = Person.objects.annotate(
        film_count=Count('film'),
        chapter_count=Count('chapter')
    ).filter(film_count=0, chapter_count__gt=0)[:10]
    
    for person in missing_people:
        print(f'- "{person.full_name()}": {person.chapter_count} chapters')

if __name__ == "__main__":
    analyze_people_directory()