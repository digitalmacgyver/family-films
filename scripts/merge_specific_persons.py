#!/usr/bin/env python3
"""
Merge Specific Persons

Usage:
    python merge_specific_persons.py <keep_person_id> <remove_person_id>

Example:
    python merge_specific_persons.py 251 260

This will merge person 260 into person 251 and delete person 260.
"""

import os
import sys
import django
import argparse

# Setup Django
sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, FilmPeople, ChapterPeople
from django.db import transaction

def merge_person(keep_person, remove_person):
    """Merge remove_person into keep_person (from person_manager.py)"""
    print(f"\nMerging person ID {remove_person.id} into ID {keep_person.id}")
    print(f"  '{remove_person.first_name} {remove_person.last_name}' -> '{keep_person.first_name} {keep_person.last_name}'")
    
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
            print(f"    + Film '{film_person.film.title}' moved to person {keep_person.id}")
    
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
            print(f"    + Chapter '{chapter_person.chapter.title}' moved to person {keep_person.id}")
    
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

def main():
    parser = argparse.ArgumentParser(description='Merge one person into another')
    parser.add_argument('keep_id', type=int, help='ID of person to keep')
    parser.add_argument('remove_id', type=int, help='ID of person to remove (will be merged into keep_id)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    print(f"=== MERGING PERSON {args.remove_id} INTO PERSON {args.keep_id} ===")
    
    try:
        # Get the persons
        keep_person = Person.objects.get(id=args.keep_id)
        remove_person = Person.objects.get(id=args.remove_id)
        
        print(f"Keep person ({args.keep_id}): '{keep_person.first_name} {keep_person.last_name}'")
        print(f"Remove person ({args.remove_id}): '{remove_person.first_name} {remove_person.last_name}'")
        
        # Show current relationships
        keep_films = FilmPeople.objects.filter(person=keep_person).count()
        keep_chapters = ChapterPeople.objects.filter(person=keep_person).count()
        remove_films = FilmPeople.objects.filter(person=remove_person).count()
        remove_chapters = ChapterPeople.objects.filter(person=remove_person).count()
        
        print(f"\nBefore merge:")
        print(f"  Person {args.keep_id}: {keep_films} films, {keep_chapters} chapters")
        print(f"  Person {args.remove_id}: {remove_films} films, {remove_chapters} chapters")
        
        if args.dry_run:
            print("\n[DRY RUN] Would merge the following:")
            print(f"  - Move {remove_films} film relationships")
            print(f"  - Move {remove_chapters} chapter relationships")
            print(f"  - Delete person {args.remove_id}")
            print("\nNo changes made.")
            return 0
        
        # Confirm the merge
        print(f"\nThis will merge all relationships from person {args.remove_id} into person {args.keep_id}")
        print(f"and permanently delete person {args.remove_id}.")
        response = input("Continue? (y/N): ")
        
        if response.lower() != 'y':
            print("Merge cancelled.")
            return 0
        
        # Perform the merge
        with transaction.atomic():
            success = merge_person(keep_person, remove_person)
        
        if success:
            # Show final count
            final_films = FilmPeople.objects.filter(person=keep_person).count()
            final_chapters = ChapterPeople.objects.filter(person=keep_person).count()
            print(f"\nAfter merge:")
            print(f"  Person {args.keep_id} now has: {final_films} films, {final_chapters} chapters")
            print(f"\n✅ Successfully merged person {args.remove_id} into person {args.keep_id}!")
        else:
            print(f"\n❌ Merge failed!")
            return 1
            
    except Person.DoesNotExist as e:
        print(f"❌ Person not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error during merge: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())