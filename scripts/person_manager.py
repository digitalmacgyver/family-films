#!/usr/bin/env python
"""
Comprehensive Person Management Tool

This script consolidates all person-related functionality:
- Find and merge duplicate people
- Normalize person names based on predefined rules
- Update person names from CSV files
- Remove orphaned people with no associations
- Apply standard family name conventions
- Fix typos and add missing last names
"""

import os
import sys
import django
import csv
import argparse
from collections import defaultdict

# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from main.models import Person, Film, Chapter, FilmPeople, ChapterPeople
from django.db import transaction
from django.db.models import Count, Q

# Standard name mappings for known family members
STANDARD_NAME_MAPPINGS = {
    ("Arlene", ""): ("Arlene", "Wren (nee Myre)"),
    ("Barabara", ""): ("Barbara", "Myre"),  # Fix typo
    ("Bob", ""): ("Bob", "Lindner"),
    ("Clarence", ""): ("Clarence", "Hayward"),
    ("David", ""): ("David", "Myer"),
    ("David", "Hayward"): ("David", "Hayward"),
    ("Earl", ""): ("Earl", "Hayward Sr."),
    ("Earl", "Hayward"): ("Earl", "Hayward Sr."),
    ("Gerry", ""): ("Gerry", "Wren"),
    ("Irwin", ""): ("Irwin", "Wren"),
    ("Irwin", "Wren"): ("Irwin", "Wren"),
    ("Iwrin", "Wren"): ("Irwin", "Wren"),  # Fix typo
    ("John", ""): ("John", "Hayward Sr."),
    ("John", "Hayward"): ("John", "Hayward Sr."),
    ("John", "Hayward Sr."): ("John", "Hayward Sr."),
    ("Joy", ""): ("Joy", "Hayward (nee Myre)"),
    ("Kathleen", ""): ("Kathleen", "Hayward"),
    ("Louise", ""): ("Louise", "Hayward"),
    ("Marion", ""): ("Marion", "Myre"),
    ("Oscar", ""): ("Oscar", "Myre"),
    ("Ruth", ""): ("Ruth", "Traylor (nee Hayward)"),
    ("Ruth", "Hayward"): ("Ruth", "Traylor (nee Hayward)"),
    ("Stan", ""): ("Stan", "Wren"),
    ("Victor", ""): ("Victor", "Beattie"),
    ("Victor", "Beattie"): ("Victor", "Beattie"),
}

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

def merge_all_duplicates(dry_run=False):
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
    
    if dry_run:
        print("\n[DRY RUN] No changes will be made.")
        return
    
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

def normalize_names(dry_run=False):
    """Normalize person names based on standard mappings."""
    print("=== Normalizing Person Names ===\n")
    
    changes_made = 0
    
    with transaction.atomic():
        for person in Person.objects.all():
            current_key = (person.first_name, person.last_name)
            
            if current_key in STANDARD_NAME_MAPPINGS:
                new_first, new_last = STANDARD_NAME_MAPPINGS[current_key]
                
                if person.first_name != new_first or person.last_name != new_last:
                    print(f"Updating: '{person.first_name} {person.last_name}' -> '{new_first} {new_last}'")
                    
                    if not dry_run:
                        person.first_name = new_first
                        person.last_name = new_last
                        person.save()
                    
                    changes_made += 1
    
    print(f"\n{changes_made} names normalized")
    if dry_run:
        print("[DRY RUN] No changes were saved")

def remove_orphaned_people(dry_run=False):
    """Remove people with no film or chapter associations."""
    print("=== Finding Orphaned People ===\n")
    
    # Get all people
    all_people = Person.objects.all()
    
    # Count associations
    people_with_films = set(FilmPeople.objects.values_list('person_id', flat=True).distinct())
    people_with_chapters = set(ChapterPeople.objects.values_list('person_id', flat=True).distinct())
    
    # Find orphans
    orphans = []
    for person in all_people:
        if person.id not in people_with_films and person.id not in people_with_chapters:
            orphans.append(person)
    
    if not orphans:
        print("No orphaned people found!")
        return
    
    print(f"Found {len(orphans)} orphaned people:")
    for person in orphans:
        print(f"  - {person.first_name} {person.last_name} (ID: {person.id})")
    
    if dry_run:
        print("\n[DRY RUN] No people will be deleted")
        return
    
    # Delete orphans
    print(f"\nDeleting {len(orphans)} orphaned people...")
    with transaction.atomic():
        for person in orphans:
            person.delete()
    
    print(f"✓ Deleted {len(orphans)} orphaned people")

def update_from_csv(csv_file, dry_run=False):
    """Update person names and associations from CSV file."""
    print(f"=== Updating from CSV: {csv_file} ===\n")
    
    if not os.path.exists(csv_file):
        print(f"ERROR: File {csv_file} not found")
        return
    
    updates = 0
    additions = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        with transaction.atomic():
            for row in reader:
                file_id = row.get('file_id', '').strip()
                chapter_index = row.get('chapter_index', '').strip()
                operation = row.get('operation', 'add').strip().lower()
                old_names = row.get('old_people', '').strip()
                new_names = row.get('new_people', '').strip()
                replace = row.get('replace', 'false').strip().lower() == 'true'
                
                if not file_id:
                    continue
                
                print(f"\nProcessing {file_id}" + (f" Chapter {chapter_index}" if chapter_index else ""))
                
                # Parse new names
                new_people = []
                if new_names:
                    for name in new_names.split(';'):
                        name = name.strip()
                        if ':' in name and not name.count(':') == 1:
                            # Handle special case like "5:25" in name
                            parts = name.split(' ', 1)
                            if len(parts) == 2:
                                new_people.append((parts[0], parts[1]))
                            else:
                                new_people.append((name, ''))
                        elif ':' in name:
                            parts = name.split(':', 1)
                            new_people.append((parts[0].strip(), parts[1].strip()))
                        else:
                            parts = name.split(' ', 1)
                            if len(parts) == 2:
                                new_people.append((parts[0], parts[1]))
                            else:
                                new_people.append((name, ''))
                
                # Get film or chapter
                try:
                    film = Film.objects.get(file_id=file_id)
                    
                    if chapter_index:
                        chapter = film.chapters.filter(index=int(chapter_index)).first()
                        if not chapter:
                            print(f"  WARNING: Chapter {chapter_index} not found")
                            continue
                        target = chapter
                        people_model = ChapterPeople
                        people_field = 'chapter'
                    else:
                        target = film
                        people_model = FilmPeople
                        people_field = 'film'
                    
                    # Handle replace mode
                    if replace and not dry_run:
                        kwargs = {people_field: target}
                        people_model.objects.filter(**kwargs).delete()
                        print(f"  Removed all existing people")
                    
                    # Add new people
                    for first_name, last_name in new_people:
                        # Check standard mappings
                        key = (first_name, last_name)
                        if key in STANDARD_NAME_MAPPINGS:
                            first_name, last_name = STANDARD_NAME_MAPPINGS[key]
                        
                        person, created = Person.objects.get_or_create(
                            first_name=first_name,
                            last_name=last_name
                        )
                        
                        if created:
                            print(f"  Created new person: {first_name} {last_name}")
                        
                        # Add association
                        kwargs = {people_field: target, 'person': person}
                        if not people_model.objects.filter(**kwargs).exists():
                            if not dry_run:
                                people_model.objects.create(**kwargs)
                            print(f"  Added: {first_name} {last_name}")
                            additions += 1
                        else:
                            print(f"  Already exists: {first_name} {last_name}")
                    
                    updates += 1
                    
                except Film.DoesNotExist:
                    print(f"  ERROR: Film {file_id} not found")
    
    print(f"\n=== Summary ===")
    print(f"Processed {updates} entries, added {additions} person associations")
    if dry_run:
        print("[DRY RUN] No changes were saved")

def analyze_people_directory():
    """Analyze people directory associations and identify missing people."""
    print("=== People Directory Analysis ===\n")
    
    # Check association patterns
    print("=== People Association Analysis ===")
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
    if fixed_query_count > current_query_count:
        print('\n=== Examples of Missing People (Chapter-only) ===')
        missing_people = Person.objects.annotate(
            film_count=Count('film'),
            chapter_count=Count('chapter')
        ).filter(film_count=0, chapter_count__gt=0)[:10]
        
        for person in missing_people:
            chapter_count = ChapterPeople.objects.filter(person=person).count()
            print(f'- "{person.first_name} {person.last_name}": {chapter_count} chapters')

def show_statistics():
    """Show statistics about people in the database."""
    print("=== Person Statistics ===\n")
    
    total_people = Person.objects.count()
    people_with_films = FilmPeople.objects.values('person').distinct().count()
    people_with_chapters = ChapterPeople.objects.values('person').distinct().count()
    
    # People with both
    film_people_ids = set(FilmPeople.objects.values_list('person_id', flat=True).distinct())
    chapter_people_ids = set(ChapterPeople.objects.values_list('person_id', flat=True).distinct())
    people_with_both = len(film_people_ids & chapter_people_ids)
    people_with_either = len(film_people_ids | chapter_people_ids)
    orphaned = total_people - people_with_either
    
    print(f"Total people: {total_people}")
    print(f"People in films only: {people_with_films - people_with_both}")
    print(f"People in chapters only: {people_with_chapters - people_with_both}")
    print(f"People in both films and chapters: {people_with_both}")
    print(f"Orphaned people (no associations): {orphaned}")
    
    # Show top people by associations
    print("\n=== Top 10 People by Film Count ===")
    top_by_films = Person.objects.annotate(
        film_count=Count('filmpeople')
    ).exclude(film_count=0).order_by('-film_count')[:10]
    
    for person in top_by_films:
        chapter_count = ChapterPeople.objects.filter(person=person).count()
        print(f"{person.first_name} {person.last_name}: {person.film_count} films, {chapter_count} chapters")
    
    # Check for duplicates
    duplicates = find_duplicate_people()
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} groups of duplicate names")
    else:
        print("\n✓ No duplicate names found")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive person management tool')
    parser.add_argument('command', choices=['merge-duplicates', 'normalize', 'remove-orphans', 
                                           'update-csv', 'statistics', 'analyze', 'all'],
                        help='Command to run')
    parser.add_argument('--csv-file', default='name_cleanup.csv', 
                        help='CSV file for update-csv command')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.command == 'merge-duplicates':
        merge_all_duplicates(dry_run=args.dry_run)
    elif args.command == 'normalize':
        normalize_names(dry_run=args.dry_run)
    elif args.command == 'remove-orphans':
        remove_orphaned_people(dry_run=args.dry_run)
    elif args.command == 'update-csv':
        update_from_csv(args.csv_file, dry_run=args.dry_run)
    elif args.command == 'statistics':
        show_statistics()
    elif args.command == 'analyze':
        analyze_people_directory()
    elif args.command == 'all':
        # Run all cleanup operations in order
        print("Running all person cleanup operations...\n")
        normalize_names(dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        merge_all_duplicates(dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        remove_orphaned_people(dry_run=args.dry_run)
        print("\n" + "="*60 + "\n")
        show_statistics()

if __name__ == "__main__":
    main()