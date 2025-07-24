#!/usr/bin/env python
"""
Script to normalize person names in the database according to specific rules.
This script will update existing Person records and their associations.
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

# Define the name mappings
NAME_MAPPINGS = [
    # (old_first_name, old_last_name, new_first_name, new_last_name)
    ("John", "", "John", "Hayward Sr."),
    ("John", "Sr", "John", "Hayward Sr."),
    ("John", "Hayward Sr.", "John", "Hayward Sr."),  # Already correct
    ("John Jr", "", "John", "Hayward Jr."),
    ("John", "Jr", "John", "Hayward Jr."),
    ("John", "Jr.", "John", "Hayward Jr."),
    ("Ruth", "", "Ruth", "Traylor (nee Hayward)"),
    ("Joy", "", "Joy", "Hofer (nee Hayward)"),
    ("Joy", "Hayward", "Joy", "Hofer (nee Hayward)"),
    ("Mark", "", "Mark", "Hayward"),
    ("Mark", "Hayward", "Mark", "Hayward"),  # Already correct
    ("James", "", "James", "Hayward"),
    ("James", "and", "James", "Hayward"),  # Fix the weird "and" last name
    ("Josephine", "Hayward", "Josephine", "Hayward (nee Myre)"),
    ("Josephine", "Hayward (nee Myre)", "Josephine", "Hayward (nee Myre)"),  # Already correct
    ("Rosabell", "Hayward", "Rosabell", "Hayward"),  # Already correct
    ("Oscar", "Myre", "Oscar", "Myre"),  # Already correct
]

def merge_duplicate_people(target_person, duplicate_people):
    """Merge duplicate people into the target person."""
    with transaction.atomic():
        for dup in duplicate_people:
            if dup.id == target_person.id:
                continue
            
            # Get existing film associations for target person
            target_film_ids = set(FilmPeople.objects.filter(person=target_person).values_list('film_id', flat=True))
            
            # Update FilmPeople references only if they won't create duplicates
            for film_person in FilmPeople.objects.filter(person=dup):
                if film_person.film_id not in target_film_ids:
                    film_person.person = target_person
                    film_person.save()
                else:
                    # Delete duplicate association
                    film_person.delete()
            
            # Get existing chapter associations for target person
            target_chapter_ids = set(ChapterPeople.objects.filter(person=target_person).values_list('chapter_id', flat=True))
            
            # Update ChapterPeople references only if they won't create duplicates
            for chapter_person in ChapterPeople.objects.filter(person=dup):
                if chapter_person.chapter_id not in target_chapter_ids:
                    chapter_person.person = target_person
                    chapter_person.save()
                else:
                    # Delete duplicate association
                    chapter_person.delete()
            
            # Delete the duplicate person
            print(f"  - Merging and deleting duplicate: {dup.full_name()} (ID: {dup.id})")
            dup.delete()

def normalize_person_names():
    """Normalize person names according to the mapping rules."""
    
    print("Starting person name normalization...")
    
    for old_first, old_last, new_first, new_last in NAME_MAPPINGS:
        print(f"\nProcessing: {old_first} {old_last} -> {new_first} {new_last}")
        
        # Find all people matching the old name
        people = Person.objects.filter(first_name=old_first, last_name=old_last)
        
        if not people.exists():
            print(f"  - No people found with name: {old_first} {old_last}")
            continue
        
        # Check if target person already exists
        target_people = Person.objects.filter(first_name=new_first, last_name=new_last)
        
        if target_people.exists():
            # Use the existing target person
            target_person = target_people.first()
            print(f"  - Target person already exists: {target_person.full_name()} (ID: {target_person.id})")
            
            # If the names are the same, check for duplicates
            if old_first == new_first and old_last == new_last:
                if target_people.count() > 1:
                    # Merge duplicates into the first one
                    duplicates = list(target_people[1:])
                    merge_duplicate_people(target_person, duplicates)
            else:
                # Merge the old people into the target
                merge_duplicate_people(target_person, people)
        else:
            # Update the first person to have the new name
            person = people.first()
            with transaction.atomic():
                person.first_name = new_first
                person.last_name = new_last
                person.save()
                print(f"  - Updated: {old_first} {old_last} -> {person.full_name()} (ID: {person.id})")
                
                # If there are duplicates with the old name, merge them
                if people.count() > 1:
                    duplicates = list(people[1:])
                    merge_duplicate_people(person, duplicates)
    
    # Final check for any remaining duplicates with the new names
    print("\nChecking for any remaining duplicates...")
    for _, _, new_first, new_last in NAME_MAPPINGS:
        people = Person.objects.filter(first_name=new_first, last_name=new_last)
        if people.count() > 1:
            print(f"\nFound {people.count()} people named {new_first} {new_last}")
            target_person = people.first()
            duplicates = list(people[1:])
            merge_duplicate_people(target_person, duplicates)
    
    print("\nPerson name normalization complete!")
    
    # Print summary
    print("\nSummary of normalized people:")
    for _, _, new_first, new_last in NAME_MAPPINGS:
        people = Person.objects.filter(first_name=new_first, last_name=new_last)
        if people.exists():
            person = people.first()
            film_count = person.film_set.count()
            chapter_count = person.chapter_set.count()
            print(f"  - {person.full_name()}: {film_count} films, {chapter_count} chapters")

if __name__ == "__main__":
    normalize_person_names()