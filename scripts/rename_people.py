#!/usr/bin/env python
"""
Script to rename specific people in the database by updating their first_name and last_name fields.
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
from django.db import transaction

def rename_person(old_first, old_last, new_first, new_last):
    """Rename a person by updating their first_name and last_name."""
    try:
        person = Person.objects.get(first_name=old_first, last_name=old_last)
        old_name = person.full_name()
        
        with transaction.atomic():
            person.first_name = new_first
            person.last_name = new_last
            person.save()
            
        print(f"✓ Renamed: '{old_name}' → '{person.full_name()}' (ID: {person.id})")
        
        # Show film and chapter counts
        film_count = person.film_set.count()
        chapter_count = person.chapter_set.count()
        print(f"  Associated with {film_count} films and {chapter_count} chapters")
        
    except Person.DoesNotExist:
        print(f"✗ Person not found: '{old_first} {old_last}'")
    except Person.MultipleObjectsReturned:
        people = Person.objects.filter(first_name=old_first, last_name=old_last)
        print(f"✗ Multiple people found with name '{old_first} {old_last}' ({people.count()} entries)")
        for p in people:
            print(f"  - ID: {p.id}, Films: {p.film_set.count()}, Chapters: {p.chapter_set.count()}")

def rename_people():
    """Rename the specified people."""
    print("Renaming people in the database...\n")
    
    # Define the renames
    renames = [
        ("Arlene", "", "Arlene", "Wren (nee Myre)"),
        ("Barabara", "", "Barbara", "Myre"),  # Note: CSV had "Barabara" (typo)
        ("Barbara", "", "Barbara", "Myre"),  # Also check correct spelling
        ("Earl", "", "Earl", "Hayward"),
    ]
    
    for old_first, old_last, new_first, new_last in renames:
        print(f"Processing: {old_first} {old_last} → {new_first} {new_last}")
        rename_person(old_first, old_last, new_first, new_last)
        print()
    
    print("Rename operation complete!")

def show_similar_names():
    """Show people with similar names to help debug."""
    print("\n=== People with similar names ===")
    
    # Look for Arlene variations
    arlenes = Person.objects.filter(first_name__icontains="Arlene")
    if arlenes:
        print("Arlene variations:")
        for person in arlenes:
            print(f"  - '{person.full_name()}' (ID: {person.id})")
    
    # Look for Barbara/Barabara variations
    barbaras = Person.objects.filter(first_name__icontains="Barbar")
    if barbaras:
        print("Barbara variations:")
        for person in barbaras:
            print(f"  - '{person.full_name()}' (ID: {person.id})")
    
    # Look for Earl variations
    earls = Person.objects.filter(first_name__icontains="Earl")
    if earls:
        print("Earl variations:")
        for person in earls:
            print(f"  - '{person.full_name()}' (ID: {person.id})")

if __name__ == "__main__":
    show_similar_names()
    rename_people()