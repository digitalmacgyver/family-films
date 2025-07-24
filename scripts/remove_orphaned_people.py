#!/usr/bin/env python
"""
Script to find and remove people that are not associated with any films or chapters.
"""

import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, Film, Chapter, FilmPeople, ChapterPeople
from django.db import transaction
from django.db.models import Q

def find_orphaned_people():
    """Find people with no film or chapter associations."""
    # Get all people
    all_people = Person.objects.all()
    
    orphaned_people = []
    
    for person in all_people:
        # Check if person has any film associations
        has_films = FilmPeople.objects.filter(person=person).exists()
        
        # Check if person has any chapter associations
        has_chapters = ChapterPeople.objects.filter(person=person).exists()
        
        # If neither, it's orphaned
        if not has_films and not has_chapters:
            orphaned_people.append(person)
    
    return orphaned_people

def remove_orphaned_people(dry_run=True):
    """Remove people that have no associations."""
    print("Finding orphaned people...")
    
    orphaned_people = find_orphaned_people()
    
    if not orphaned_people:
        print("No orphaned people found!")
        return
    
    print(f"\nFound {len(orphaned_people)} orphaned people:")
    for person in orphaned_people:
        print(f"  - {person.full_name()} (ID: {person.id})")
    
    if dry_run:
        print("\n[DRY RUN] No people were deleted. Run with dry_run=False to actually delete.")
    else:
        print("\nDeleting orphaned people...")
        with transaction.atomic():
            for person in orphaned_people:
                person.delete()
                print(f"  ✓ Deleted: {person.full_name()}")
        print(f"\nSuccessfully deleted {len(orphaned_people)} orphaned people.")

def print_people_stats():
    """Print statistics about people."""
    total_people = Person.objects.count()
    
    # People with film associations
    people_with_films = Person.objects.filter(
        film__isnull=False
    ).distinct().count()
    
    # People with chapter associations
    people_with_chapters = Person.objects.filter(
        chapter__isnull=False
    ).distinct().count()
    
    # People with any associations
    people_with_any = Person.objects.filter(
        Q(film__isnull=False) | Q(chapter__isnull=False)
    ).distinct().count()
    
    print("\n=== People Statistics ===")
    print(f"Total people: {total_people}")
    print(f"People with film associations: {people_with_films}")
    print(f"People with chapter associations: {people_with_chapters}")
    print(f"People with any associations: {people_with_any}")
    print(f"Orphaned people: {total_people - people_with_any}")

if __name__ == "__main__":
    import sys
    
    # Check for command line argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        dry_run = False
    
    print_people_stats()
    print("\n" + "="*50 + "\n")
    remove_orphaned_people(dry_run=dry_run)
    
    if dry_run:
        print("\nTo actually delete orphaned people, run:")
        print(f"  python {sys.argv[0]} --delete")