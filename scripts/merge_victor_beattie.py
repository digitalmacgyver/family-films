#!/usr/bin/env python
"""
Script to merge Victor Beattie (ID 222) into Victor Beattie (ID 177).
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

def merge_victor_beattie():
    """Merge person 222 into person 177."""
    
    try:
        person_177 = Person.objects.get(id=177)
        person_222 = Person.objects.get(id=222)
    except Person.DoesNotExist as e:
        print(f"Error: {e}")
        return
    
    print(f"Merging Victor Beattie duplicate:")
    print(f"  Target (keeping): {person_177.full_name()} (ID: 177)")
    print(f"  Duplicate (removing): {person_222.full_name()} (ID: 222)")
    print()
    
    with transaction.atomic():
        # Update FilmPeople relationships
        film_relationships = FilmPeople.objects.filter(person=person_222)
        film_count = film_relationships.count()
        print(f"Found {film_count} film relationships for person 222")
        
        films_updated = 0
        films_skipped = 0
        
        for film_person in film_relationships:
            # Check if relationship already exists with person 177
            if FilmPeople.objects.filter(film=film_person.film, person=person_177).exists():
                print(f"  - Film '{film_person.film.title}' already has relationship with person 177, skipping")
                films_skipped += 1
                film_person.delete()
            else:
                # Update the relationship
                film_person.person = person_177
                film_person.save()
                print(f"  ✓ Updated film '{film_person.film.title}' to use person 177")
                films_updated += 1
        
        # Update ChapterPeople relationships
        chapter_relationships = ChapterPeople.objects.filter(person=person_222)
        chapter_count = chapter_relationships.count()
        print(f"\nFound {chapter_count} chapter relationships for person 222")
        
        chapters_updated = 0
        chapters_skipped = 0
        
        for chapter_person in chapter_relationships:
            # Check if relationship already exists with person 177
            if ChapterPeople.objects.filter(chapter=chapter_person.chapter, person=person_177).exists():
                print(f"  - Chapter '{chapter_person.chapter.title}' already has relationship with person 177, skipping")
                chapters_skipped += 1
                chapter_person.delete()
            else:
                # Update the relationship
                chapter_person.person = person_177
                chapter_person.save()
                print(f"  ✓ Updated chapter '{chapter_person.chapter.title}' to use person 177")
                chapters_updated += 1
        
        # Delete person 222
        person_222.delete()
        print(f"\n✓ Deleted duplicate person (ID: 222)")
        
        print(f"\nSummary:")
        print(f"  Films updated: {films_updated}")
        print(f"  Films skipped (already existed): {films_skipped}")
        print(f"  Chapters updated: {chapters_updated}")
        print(f"  Chapters skipped (already existed): {chapters_skipped}")
        print(f"  Total relationships moved: {films_updated + chapters_updated}")

def verify_victor_beattie():
    """Verify the Victor Beattie entries."""
    print("\n=== Verifying Victor Beattie entries ===")
    
    # Check for Victor Beattie entries
    victor_beatties = Person.objects.filter(first_name="Victor", last_name="Beattie")
    
    print(f"Found {victor_beatties.count()} person(s) named 'Victor Beattie':")
    for person in victor_beatties:
        film_count = FilmPeople.objects.filter(person=person).count()
        chapter_count = ChapterPeople.objects.filter(person=person).count()
        print(f"  - ID: {person.id}, Films: {film_count}, Chapters: {chapter_count}")

if __name__ == "__main__":
    verify_victor_beattie()
    print("\n" + "="*50 + "\n")
    merge_victor_beattie()
    print("\n" + "="*50 + "\n")
    verify_victor_beattie()