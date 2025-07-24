#!/usr/bin/env python
"""
Comprehensive script to normalize person names in the database.
This handles additional cases like "Ruth Hayward" -> "Ruth Traylor (nee Hayward)"
and "Josephine " -> "Josephine Hayward (nee Myre)"
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, FilmPeople, ChapterPeople
from django.db import transaction

def merge_people_safely(target_person, source_person):
    """Safely merge source person into target person, handling unique constraints."""
    if target_person.id == source_person.id:
        return
        
    with transaction.atomic():
        # Get existing associations
        target_film_ids = set(FilmPeople.objects.filter(person=target_person).values_list('film_id', flat=True))
        target_chapter_ids = set(ChapterPeople.objects.filter(person=target_person).values_list('chapter_id', flat=True))
        
        # Merge film associations
        for film_person in FilmPeople.objects.filter(person=source_person):
            if film_person.film_id not in target_film_ids:
                film_person.person = target_person
                film_person.save()
            else:
                film_person.delete()
        
        # Merge chapter associations
        for chapter_person in ChapterPeople.objects.filter(person=source_person):
            if chapter_person.chapter_id not in target_chapter_ids:
                chapter_person.person = target_person
                chapter_person.save()
            else:
                chapter_person.delete()
        
        # Delete the source person
        print(f"  - Merged {source_person.full_name()} (ID: {source_person.id}) -> {target_person.full_name()} (ID: {target_person.id})")
        source_person.delete()

def normalize_additional_cases():
    """Handle additional normalization cases."""
    
    print("Handling additional person name normalizations...")
    
    # Handle "Ruth Hayward" -> "Ruth Traylor (nee Hayward)"
    try:
        ruth_hayward = Person.objects.get(first_name="Ruth", last_name="Hayward")
        ruth_traylor = Person.objects.get(first_name="Ruth", last_name="Traylor (nee Hayward)")
        merge_people_safely(ruth_traylor, ruth_hayward)
    except Person.DoesNotExist:
        pass
    
    # Handle "Josephine " (with space) -> "Josephine Hayward (nee Myre)"
    try:
        josephine_space = Person.objects.get(first_name="Josephine", last_name="")
        josephine_myre = Person.objects.get(first_name="Josephine", last_name="Hayward (nee Myre)")
        merge_people_safely(josephine_myre, josephine_space)
    except Person.DoesNotExist:
        pass
    
    # Find any person with trailing/leading spaces and clean them
    print("\nCleaning up names with extra spaces...")
    people_with_spaces = Person.objects.filter(first_name__contains=" ") | Person.objects.filter(last_name__contains=" ")
    for person in people_with_spaces:
        old_name = person.full_name()
        person.first_name = person.first_name.strip()
        person.last_name = person.last_name.strip()
        person.save()
        print(f"  - Cleaned: '{old_name}' -> '{person.full_name()}'")
    
    print("\nAdditional normalizations complete!")

def print_family_summary():
    """Print a summary of the main family members."""
    print("\n=== Family Members Summary ===")
    
    family_members = [
        ("John", "Hayward Sr."),
        ("John", "Hayward Jr."),
        ("Josephine", "Hayward (nee Myre)"),
        ("Ruth", "Traylor (nee Hayward)"),
        ("Joy", "Hofer (nee Hayward)"),
        ("Mark", "Hayward"),
        ("James", "Hayward"),
        ("Rosabell", "Hayward"),
        ("Oscar", "Myre"),
    ]
    
    for first_name, last_name in family_members:
        try:
            person = Person.objects.get(first_name=first_name, last_name=last_name)
            film_count = person.film_set.count()
            chapter_count = person.chapter_set.count()
            print(f"{person.full_name()} (ID: {person.id}): {film_count} films, {chapter_count} chapters")
        except Person.DoesNotExist:
            print(f"{first_name} {last_name}: NOT FOUND")
        except Person.MultipleObjectsReturned:
            people = Person.objects.filter(first_name=first_name, last_name=last_name)
            print(f"{first_name} {last_name}: MULTIPLE FOUND ({people.count()} entries)")

if __name__ == "__main__":
    normalize_additional_cases()
    print_family_summary()