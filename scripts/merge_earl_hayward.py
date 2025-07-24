#!/usr/bin/env python
"""
Script to merge Earl Hayward (ID 221) into Earl Hayward (ID 161).
Updates all film and chapter relationships, then removes the duplicate.
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

def merge_earl_hayward():
    """Merge person 221 into person 161."""
    
    try:
        person_161 = Person.objects.get(id=161)
        person_221 = Person.objects.get(id=221)
    except Person.DoesNotExist as e:
        print(f"Error: {e}")
        return
    
    print(f"Merging Earl Hayward duplicate:")
    print(f"  Target (keeping): {person_161.full_name()} (ID: 161)")
    print(f"  Duplicate (removing): {person_221.full_name()} (ID: 221)")
    print()
    
    with transaction.atomic():
        # Update FilmPeople relationships
        film_relationships = FilmPeople.objects.filter(person=person_221)
        film_count = film_relationships.count()
        print(f"Found {film_count} film relationships for person 221")
        
        films_updated = 0
        films_skipped = 0
        
        for film_person in film_relationships:
            # Check if relationship already exists with person 161
            if FilmPeople.objects.filter(film=film_person.film, person=person_161).exists():
                print(f"  - Film '{film_person.film.title}' already has relationship with person 161, skipping")
                films_skipped += 1
                film_person.delete()
            else:
                # Update the relationship
                film_person.person = person_161
                film_person.save()
                print(f"  ✓ Updated film '{film_person.film.title}' to use person 161")
                films_updated += 1
        
        # Update ChapterPeople relationships
        chapter_relationships = ChapterPeople.objects.filter(person=person_221)
        chapter_count = chapter_relationships.count()
        print(f"\nFound {chapter_count} chapter relationships for person 221")
        
        chapters_updated = 0
        chapters_skipped = 0
        
        for chapter_person in chapter_relationships:
            # Check if relationship already exists with person 161
            if ChapterPeople.objects.filter(chapter=chapter_person.chapter, person=person_161).exists():
                print(f"  - Chapter '{chapter_person.chapter.title}' already has relationship with person 161, skipping")
                chapters_skipped += 1
                chapter_person.delete()
            else:
                # Update the relationship
                chapter_person.person = person_161
                chapter_person.save()
                print(f"  ✓ Updated chapter '{chapter_person.chapter.title}' to use person 161")
                chapters_updated += 1
        
        # Delete person 221
        person_221.delete()
        print(f"\n✓ Deleted duplicate person (ID: 221)")
        
        print(f"\nSummary:")
        print(f"  Films updated: {films_updated}")
        print(f"  Films skipped (already existed): {films_skipped}")
        print(f"  Chapters updated: {chapters_updated}")
        print(f"  Chapters skipped (already existed): {chapters_skipped}")
        print(f"  Total relationships moved: {films_updated + chapters_updated}")

def verify_earl_hayward():
    """Verify the Earl Hayward entries."""
    print("\n=== Verifying Earl Hayward entries ===")
    
    # Check for Earl Hayward entries
    earl_haywards = Person.objects.filter(first_name="Earl", last_name="Hayward")
    
    print(f"Found {earl_haywards.count()} person(s) named 'Earl Hayward':")
    for person in earl_haywards:
        film_count = FilmPeople.objects.filter(person=person).count()
        chapter_count = ChapterPeople.objects.filter(person=person).count()
        print(f"  - ID: {person.id}, Films: {film_count}, Chapters: {chapter_count}")

if __name__ == "__main__":
    verify_earl_hayward()
    print("\n" + "="*50 + "\n")
    merge_earl_hayward()
    print("\n" + "="*50 + "\n")
    verify_earl_hayward()