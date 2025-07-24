#!/usr/bin/env python
"""
Script to find and merge all duplicate people with identical first and last names.
Merges relationships from higher ID to lower ID, then deletes duplicates.
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
from django.db.models import Count
from collections import defaultdict

def find_duplicate_people():
    """Find all people with identical first and last names."""
    # Group people by (first_name, last_name)
    name_groups = defaultdict(list)
    
    for person in Person.objects.all():
        key = (person.first_name, person.last_name)
        name_groups[key].append(person)
    
    # Find groups with more than one person
    duplicates = []
    for (first_name, last_name), people in name_groups.items():
        if len(people) > 1:
            # Sort by ID to ensure consistent ordering
            people.sort(key=lambda p: p.id)
            duplicates.append((first_name, last_name, people))
    
    return duplicates

def merge_person(keep_person, remove_person):
    """Merge remove_person into keep_person."""
    print(f"\nMerging person ID {remove_person.id} into ID {keep_person.id}")
    
    # Update FilmPeople relationships
    film_relationships = FilmPeople.objects.filter(person=remove_person)
    film_count = film_relationships.count()
    print(f"  Found {film_count} film relationships for person {remove_person.id}")
    
    films_updated = 0
    films_skipped = 0
    
    for film_person in film_relationships:
        # Check if relationship already exists with keep_person
        if FilmPeople.objects.filter(film=film_person.film, person=keep_person).exists():
            print(f"    - Film '{film_person.film.title}' already has relationship with person {keep_person.id}, skipping")
            films_skipped += 1
            film_person.delete()
        else:
            # Update the relationship
            film_person.person = keep_person
            film_person.save()
            films_updated += 1
    
    # Update ChapterPeople relationships
    chapter_relationships = ChapterPeople.objects.filter(person=remove_person)
    chapter_count = chapter_relationships.count()
    print(f"  Found {chapter_count} chapter relationships for person {remove_person.id}")
    
    chapters_updated = 0
    chapters_skipped = 0
    
    for chapter_person in chapter_relationships:
        # Check if relationship already exists with keep_person
        if ChapterPeople.objects.filter(chapter=chapter_person.chapter, person=keep_person).exists():
            print(f"    - Chapter '{chapter_person.chapter.title}' already has relationship with person {keep_person.id}, skipping")
            chapters_skipped += 1
            chapter_person.delete()
        else:
            # Update the relationship
            chapter_person.person = keep_person
            chapter_person.save()
            chapters_updated += 1
    
    # Verify no relationships remain
    remaining_films = FilmPeople.objects.filter(person=remove_person).count()
    remaining_chapters = ChapterPeople.objects.filter(person=remove_person).count()
    
    if remaining_films > 0 or remaining_chapters > 0:
        print(f"  ⚠️  WARNING: Person {remove_person.id} still has {remaining_films} films and {remaining_chapters} chapters!")
        return False
    
    # Delete the duplicate person
    remove_person.delete()
    print(f"  ✓ Deleted person ID {remove_person.id}")
    
    print(f"  Summary: {films_updated} films and {chapters_updated} chapters moved, {films_skipped + chapters_skipped} skipped")
    return True

def merge_all_duplicates():
    """Find and merge all duplicate people."""
    print("=== Finding Duplicate People ===")
    
    duplicates = find_duplicate_people()
    
    if not duplicates:
        print("No duplicate people found!")
        return
    
    print(f"\nFound {len(duplicates)} groups of duplicate people:")
    
    for first_name, last_name, people in duplicates:
        print(f"\n'{first_name} {last_name}' has {len(people)} entries:")
        for person in people:
            film_count = FilmPeople.objects.filter(person=person).count()
            chapter_count = ChapterPeople.objects.filter(person=person).count()
            print(f"  - ID: {person.id}, Films: {film_count}, Chapters: {chapter_count}")
    
    print("\n" + "="*50)
    print("=== Merging Duplicates ===")
    
    total_merged = 0
    
    with transaction.atomic():
        for first_name, last_name, people in duplicates:
            print(f"\nProcessing '{first_name} {last_name}':")
            
            # Keep the person with lowest ID
            keep_person = people[0]
            
            # Merge all others into it
            for remove_person in people[1:]:
                if merge_person(keep_person, remove_person):
                    total_merged += 1
    
    print(f"\n=== Summary ===")
    print(f"Successfully merged {total_merged} duplicate people")

def add_unique_constraint():
    """Add a unique constraint on (first_name, last_name)."""
    print("\n=== Adding Unique Constraint ===")
    
    # First verify no duplicates remain
    duplicates = find_duplicate_people()
    if duplicates:
        print("⚠️  Cannot add unique constraint - duplicates still exist!")
        return
    
    print("No duplicates found. Ready to add unique constraint.")
    print("\nTo add the unique constraint, create and run this migration:")
    print("\npython manage.py makemigrations main --name add_person_name_unique_constraint")
    print("\nThen add this to the Person model's Meta class:")
    print("    unique_together = [['first_name', 'last_name']]")

if __name__ == "__main__":
    merge_all_duplicates()
    add_unique_constraint()