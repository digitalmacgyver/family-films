#!/usr/bin/env python
"""
Script to merge Iwrin Wren (ID 216) into Irwin Wren (ID 98).
Person 216 has a typo in the first name: "Iwrin" instead of "Irwin".
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

def merge_iwrin_wren():
    """Merge person 216 (Iwrin) into person 98 (Irwin)."""
    
    try:
        person_98 = Person.objects.get(id=98)
        person_216 = Person.objects.get(id=216)
    except Person.DoesNotExist as e:
        print(f"Error: {e}")
        return
    
    print(f"Merging typo duplicate:")
    print(f"  Target (keeping): {person_98.full_name()} (ID: 98)")
    print(f"  Duplicate with typo (removing): {person_216.full_name()} (ID: 216)")
    print()
    
    with transaction.atomic():
        # Update FilmPeople relationships
        film_relationships = FilmPeople.objects.filter(person=person_216)
        film_count = film_relationships.count()
        print(f"Found {film_count} film relationships for person 216")
        
        films_updated = 0
        films_skipped = 0
        
        for film_person in film_relationships:
            # Check if relationship already exists with person 98
            if FilmPeople.objects.filter(film=film_person.film, person=person_98).exists():
                print(f"  - Film '{film_person.film.title}' already has relationship with person 98, skipping")
                films_skipped += 1
                film_person.delete()
            else:
                # Update the relationship
                film_person.person = person_98
                film_person.save()
                print(f"  ✓ Updated film '{film_person.film.title}' to use person 98")
                films_updated += 1
        
        # Update ChapterPeople relationships
        chapter_relationships = ChapterPeople.objects.filter(person=person_216)
        chapter_count = chapter_relationships.count()
        print(f"\nFound {chapter_count} chapter relationships for person 216")
        
        chapters_updated = 0
        chapters_skipped = 0
        
        for chapter_person in chapter_relationships:
            # Check if relationship already exists with person 98
            if ChapterPeople.objects.filter(chapter=chapter_person.chapter, person=person_98).exists():
                print(f"  - Chapter '{chapter_person.chapter.title}' already has relationship with person 98, skipping")
                chapters_skipped += 1
                chapter_person.delete()
            else:
                # Update the relationship
                chapter_person.person = person_98
                chapter_person.save()
                print(f"  ✓ Updated chapter '{chapter_person.chapter.title}' to use person 98")
                chapters_updated += 1
        
        # Verify no relationships remain
        remaining_films = FilmPeople.objects.filter(person=person_216).count()
        remaining_chapters = ChapterPeople.objects.filter(person=person_216).count()
        
        if remaining_films > 0 or remaining_chapters > 0:
            print(f"  ⚠️  WARNING: Person 216 still has {remaining_films} films and {remaining_chapters} chapters!")
            return False
        
        # Delete person 216
        person_216.delete()
        print(f"\n✓ Deleted person ID 216 (typo duplicate)")
        
        print(f"\nSummary:")
        print(f"  Films updated: {films_updated}")
        print(f"  Films skipped (already existed): {films_skipped}")
        print(f"  Chapters updated: {chapters_updated}")
        print(f"  Chapters skipped (already existed): {chapters_skipped}")
        print(f"  Total relationships moved: {films_updated + chapters_updated}")
        
        return True

def verify_irwin_wren():
    """Verify the Irwin Wren entries."""
    print("\n=== Verifying Irwin Wren entries ===")
    
    # Check for Irwin Wren entries (both spellings)
    irwin_wrens = Person.objects.filter(
        first_name__in=["Irwin", "Iwrin"], 
        last_name="Wren"
    )
    
    print(f"Found {irwin_wrens.count()} person(s) with similar names:")
    for person in irwin_wrens:
        film_count = FilmPeople.objects.filter(person=person).count()
        chapter_count = ChapterPeople.objects.filter(person=person).count()
        print(f"  - ID: {person.id}, Name: '{person.first_name} {person.last_name}', Films: {film_count}, Chapters: {chapter_count}")

if __name__ == "__main__":
    verify_irwin_wren()
    print("\n" + "="*50 + "\n")
    if merge_iwrin_wren():
        print("\nMerge completed successfully!")
    else:
        print("\nMerge failed!")
    print("\n" + "="*50 + "\n")
    verify_irwin_wren()